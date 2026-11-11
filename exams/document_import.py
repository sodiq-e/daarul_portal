import re
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.html import escape
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from PIL import Image, UnidentifiedImageError
from zipfile import BadZipFile


QUESTION_PATTERN = re.compile(r'^\s*(?:(?:question|q)\s*)?\d+\s*[.)]\s*', re.IGNORECASE)
OPTION_PATTERN = re.compile(r'^\s*([A-E])\s*[.)]\s*(.*)$', re.IGNORECASE)
SECTION_PATTERN = re.compile(r'^\s*(?:section\s+[A-Z0-9]+|part\s+[A-Z0-9]+)\s*[:.-]?\s*(.*)$', re.IGNORECASE)
IMAGE_FORMATS = {
    'BMP': 'bmp',
    'GIF': 'gif',
    'JPEG': 'jpg',
    'PNG': 'png',
    'WEBP': 'webp',
}


def _store_image(image_part):
    image_bytes = image_part.blob
    max_image_size = getattr(settings, 'EXAM_IMPORT_MAX_IMAGE_SIZE', 5 * 1024 * 1024)
    if len(image_bytes) > max_image_size:
        raise ValueError('An embedded image exceeds the allowed size.')

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            image.verify()
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError) as error:
        raise ValueError('The Word document contains an unsupported or invalid image.') from error

    extension = IMAGE_FORMATS.get(image_format)
    if not extension:
        raise ValueError('The Word document contains an unsupported image format.')

    path = default_storage.save(
        f'exam_resources/{uuid.uuid4().hex}.{extension}',
        ContentFile(image_bytes),
    )
    return default_storage.url(path)


def _paragraph_html(paragraph, image_urls, strip_question_number=False):
    content = []
    first_text = True
    for run in paragraph.runs:
        text = run.text
        if strip_question_number and first_text:
            text = QUESTION_PATTERN.sub('', text, count=1)
            first_text = False

        rendered = escape(text).replace('\n', '<br>')
        if run.bold:
            rendered = f'<strong>{rendered}</strong>'
        if run.italic:
            rendered = f'<em>{rendered}</em>'
        if run.underline:
            rendered = f'<u>{rendered}</u>'
        content.append(rendered)

        for blip in run._element.xpath('.//a:blip'):
            relationship_id = blip.get(qn('r:embed'))
            if not relationship_id:
                continue
            if relationship_id not in image_urls:
                image_urls[relationship_id] = _store_image(
                    run.part.related_parts[relationship_id]
                )
            content.append(
                f'<img src="{escape(image_urls[relationship_id])}" alt="">'
            )

    body = ''.join(content)
    if not body:
        return ''

    alignment = paragraph.alignment
    alignments = {
        0: 'left',
        1: 'center',
        2: 'right',
        3: 'justify',
    }
    align_style = alignments.get(alignment)
    style = f' style="text-align:{align_style}"' if align_style else ''
    return f'<p{style}>{body}</p>'


def _table_html(table, image_urls):
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            paragraphs = [
                _paragraph_html(paragraph, image_urls)
                for paragraph in cell.paragraphs
            ]
            cells.append(f'<td>{"".join(paragraphs)}</td>')
        rows.append(f'<tr>{"".join(cells)}</tr>')
    return f'<table><tbody>{"".join(rows)}</tbody></table>'


def _document_blocks(document, image_urls):
    for child in document.element.body.iterchildren():
        if child.tag == qn('w:p'):
            paragraph = Paragraph(child, document)
            html = _paragraph_html(
                paragraph,
                image_urls,
                strip_question_number=bool(QUESTION_PATTERN.match(paragraph.text.strip())),
            )
            if html:
                yield paragraph.text.strip(), html, paragraph.style.name
        elif child.tag == qn('w:tbl'):
            table = Table(child, document)
            html = _table_html(table, image_urls)
            if html:
                text = ' '.join(
                    cell.text.strip()
                    for row in table.rows
                    for cell in row.cells
                    if cell.text.strip()
                )
                yield text, html, ''


def import_docx(uploaded_file, mode):
    if mode not in {'editable_questions', 'preserve_document'}:
        raise ValueError('Choose a valid Word import mode.')

    try:
        document = Document(uploaded_file)
    except (BadZipFile, PackageNotFoundError, ValueError) as error:
        raise ValueError('The uploaded file is not a valid .docx document.') from error
    image_urls = {}
    blocks = list(_document_blocks(document, image_urls))
    if not blocks:
        raise ValueError('The Word document does not contain any readable content.')

    if mode == 'preserve_document':
        return [{
            'title': 'Imported Document',
            'section_type': 'theory',
            'instruction': '',
            'marks_allocation': 0,
            'font_family': 'Arial',
            'font_size': '12pt',
            'questions': [{
                'question_text': ''.join(html for _, html, _ in blocks),
                'question_type': 'theory',
                'marks': '',
                'options': [],
            }],
        }]

    sections = []

    def new_section(title='Imported Questions', section_type='theory'):
        section = {
            'title': title,
            'section_type': section_type,
            'instruction': '',
            'marks_allocation': 0,
            'font_family': 'Arial',
            'font_size': '12pt',
            'questions': [],
        }
        sections.append(section)
        return section

    current_section = new_section()
    current_question = None
    preamble = []
    for text, html, style_name in blocks:
        section_heading = SECTION_PATTERN.match(text)
        if style_name.lower().startswith('heading') or section_heading:
            title = section_heading.group(1).strip() if section_heading else text
            if (
                current_section['title'] != 'Imported Questions' or
                current_section['questions'] or
                current_section['instruction']
            ):
                current_section = new_section(title or text)
            else:
                current_section['title'] = title or text
            current_question = None
            continue

        option_match = OPTION_PATTERN.match(text)
        if option_match and current_question:
            current_question['options'].append({
                'option_label': option_match.group(1).upper(),
                'option_text': option_match.group(2).strip(),
            })
            current_question['question_type'] = 'objective'
            current_section['section_type'] = 'objective'
            continue

        question_match = QUESTION_PATTERN.match(text)
        if question_match:
            current_question = {
                'question_text': html,
                'question_type': 'theory',
                'marks': '',
                'options': [],
            }
            current_section['questions'].append(current_question)
            continue

        if current_question:
            current_question['question_text'] += html
        else:
            preamble.append(text)

    if not any(section['questions'] for section in sections):
        current_section['questions'] = [
            {
                'question_text': html,
                'question_type': 'theory',
                'marks': '',
                'options': [],
            }
            for _, html, _ in blocks
        ]
    elif preamble:
        sections[0]['instruction'] = '\n'.join(preamble)

    return sections
