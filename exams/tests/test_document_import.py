import json
from html.parser import HTMLParser
from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.template.loader import render_to_string
from docx import Document
from PIL import Image

from exams.document_import import import_docx
from exams.export_utils import export_exam_to_pdf_html
from exams.views import ExamPaperImportView


def make_docx():
    document = Document()
    document.add_heading('Section A: Multiple Choice', level=1)
    document.add_paragraph('1. Which colour is shown?')
    document.add_paragraph('A. Blue')
    document.add_paragraph('B. Green')
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


class ExamDocumentImportTests(SimpleTestCase):
    def test_builder_json_values_survive_html_attribute_rendering(self):
        rendered = render_to_string('exams/teacher_exam_form.html', {
            'exam_json': json.dumps({'sections': [], 'subject': 12}),
            'class_subject_map': json.dumps({'4': [{'id': 12, 'name': 'Values & Health'}]}),
            'save_draft_url': '/exams/exam-papers/save-draft/',
            'submit_url': '/exams/exam-papers/submit/',
            'import_document_url': '/exams/exam-papers/import-document/',
            'preview_url_template': '/exams/papers/0/preview/',
            'page_title': 'Edit Exam Paper',
        })

        class HiddenInputParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.values = {}

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == 'input' and attributes.get('id') in {'exam-json', 'class-subject-map'}:
                    self.values[attributes['id']] = attributes.get('value')

        parser = HiddenInputParser()
        parser.feed(rendered)

        self.assertEqual(json.loads(parser.values['exam-json']), {'sections': [], 'subject': 12})
        self.assertEqual(
            json.loads(parser.values['class-subject-map']),
            {'4': [{'id': 12, 'name': 'Values & Health'}]},
        )

    def test_builder_config_is_rendered_inside_template_inheritance(self):
        rendered = render_to_string('exams/teacher_exam_form.html', {
            'exam_json': '{}',
            'class_subject_map': '{}',
            'save_draft_url': '/exams/exam-papers/save-draft/',
            'submit_url': '/exams/exam-papers/submit/',
            'import_document_url': '/exams/exam-papers/import-document/',
            'preview_url_template': '/exams/papers/0/preview/',
            'page_title': 'Create Exam Paper',
            'csrf_token': 'test-token',
        })

        self.assertIn('id="preview-url-template" value="/exams/papers/0/preview/"', rendered)
        self.assertIn('id="exam-json" value="{}"', rendered)

    def test_diagrams_can_be_resized_and_inserted_inline_or_on_their_own_line(self):
        rendered = render_to_string('exams/teacher_exam_form.html', {
            'exam_json': '{}',
            'class_subject_map': '{}',
            'save_draft_url': '/exams/exam-papers/save-draft/',
            'submit_url': '/exams/exam-papers/submit/',
            'import_document_url': '/exams/exam-papers/import-document/',
            'preview_url_template': '/exams/papers/0/preview/',
            'page_title': 'Create Exam Paper',
        })

        self.assertIn('class="diagram-width" min="20" max="1200" value="180"', rendered)
        self.assertIn('class="diagram-width-slider" min="20" max="600" step="5" value="180"', rendered)
        self.assertIn('<option value="inline" selected>In the paragraph</option>', rendered)
        self.assertIn('<option value="block">Own line</option>', rendered)
        self.assertIn("options.placement === 'inline' ? 'imageInline' : 'imageBlock'", rendered)
        self.assertIn("editor.execute('insertImage', { source: url })", rendered)
        self.assertIn('render-diagram-size">Render size</button>', rendered)
        self.assertIn('class="diagram-render-preview" hidden', rendered)
        self.assertIn('preview.dataset.diagramUrl = url;', rendered)
        self.assertIn('preview.textContent = `Diagram in the editor:', rendered)
        self.assertNotIn('<img alt="Diagram size preview"', rendered)
        self.assertIn("editor.model.document.getRoot()", rendered)
        self.assertIn('function resizeImageDataURL(source, width)', rendered)
        self.assertIn('canvas.height = Math.max(1, Math.round(image.naturalHeight * canvas.width / image.naturalWidth));', rendered)
        self.assertIn("writer.setAttribute('src', newUrl, image)", rendered)
        self.assertNotIn('resizedWidth', rendered)
        self.assertIn('const resizedDataURL = await resizeImageDataURL(dataURL, options.width);', rendered)
        self.assertIn('if (insertImageUrl(editor, options.textarea, result.url, options, insertionSelection)) {', rendered)
        self.assertIn('const saved = await saveDraft();', rendered)
        self.assertIn('window.addEventListener(\'mouseup\', this.handleWindowMouseUp)', rendered)
        self.assertIn('const shapes = Array.from(this.layer.getChildren()).filter(shape => !shape._isPreview);', rendered)
        self.assertIn('const exportStage = new Konva.Stage({', rendered)
        self.assertIn('shapes.forEach(shape => drawingGroup.add(shape.clone({ listening: false })));', rendered)
        self.assertIn('return exportStage.toDataURL({ pixelRatio: 2 });', rendered)
        self.assertNotIn('return this.layer.toDataURL({', rendered)
        self.assertNotIn('return this.stage.toDataURL({ pixelRatio: 2 });', rendered)
        self.assertIn('this.finishDrawing();', rendered)
        self.assertIn('touch-action: none;', rendered)
        self.assertIn('document.body.style.overflow = \'hidden\';', rendered)
        self.assertIn('document.documentElement.appendChild(modal);', rendered)
        self.assertIn('this.resizeObserver = new ResizeObserver(() => this.resizeToContainer());', rendered)
        self.assertIn('this.resizeObserver.disconnect();', rendered)
        self.assertIn('this.stage.size({ width, height });', rendered)
        self.assertIn('this.gridLayer.listening(false);', rendered)

        preview_template = render_to_string('exams/exam_paper_preview.html', {
            'exam': SimpleNamespace(
                pk=1, school_class='Class 1', subject='Mathematics', duration='1 hour',
                term='First Term', academic_session='2026/2027', scoring_enabled=False,
                total_marks=100, instructions='',
            ),
            'sections_data': [],
        })
        self.assertIn('.exam-paper-question-content figure.image', preview_template)
        self.assertIn('.exam-paper-question-content figure.image img', preview_template)
        self.assertIn('max-width: 120px !important;', preview_template)
        self.assertIn('max-height: 90px !important;', preview_template)

        print_template = render_to_string('exams/print_exam_paper.html', {
            'exam_paper': SimpleNamespace(
                pk=1, school_class='Class 1', subject='Mathematics', duration='1 hour',
                term='First Term', academic_session='2026/2027', scoring_enabled=False,
                total_marks=100, instructions='',
            ),
            'sections_data': [],
        })
        self.assertIn('.exam-paper-question-content figure.image', print_template)
        self.assertIn('max-width: 120px !important;', print_template)
        self.assertIn('max-height: 90px !important;', print_template)

    def test_scoring_controls_are_opt_in_and_student_preview_hides_disabled_marks(self):
        rendered_form = render_to_string('exams/teacher_exam_form.html', {
            'exam_json': '{}',
            'class_subject_map': '{}',
            'save_draft_url': '/exams/exam-papers/save-draft/',
            'submit_url': '/exams/exam-papers/submit/',
            'import_document_url': '/exams/exam-papers/import-document/',
            'preview_url_template': '/exams/papers/0/preview/',
            'page_title': 'Create Exam Paper',
        })
        self.assertIn('id="id_scoring_enabled" type="checkbox"', rendered_form)
        self.assertIn('class="col-lg-4 scoring-field"', rendered_form)
        self.assertIn('scoring_enabled: scoringEnabled', rendered_form)

        exam = SimpleNamespace(
            pk=1,
            school_class='Class 1',
            subject='Mathematics',
            duration='1 hour',
            term='First Term',
            academic_session='2026/2027',
            scoring_enabled=False,
            total_marks=100,
            instructions='',
        )
        rendered_preview = render_to_string('exams/exam_paper_preview.html', {
            'exam': exam,
            'sections_data': [],
        })
        self.assertNotIn('<strong>Total Marks:</strong>', rendered_preview)

        exam.scoring_enabled = True
        rendered_preview = render_to_string('exams/exam_paper_preview.html', {
            'exam': exam,
            'sections_data': [],
        })
        self.assertIn('<strong>Total Marks:</strong> 100', rendered_preview)

    def test_pdf_export_suppresses_marks_when_scoring_is_disabled(self):
        question = SimpleNamespace(
            question_text='Question',
            marks=5,
            teacher_guide='',
            options=SimpleNamespace(all=lambda: []),
        )
        section = SimpleNamespace(
            get_section_type_display=lambda: 'Theory',
            title='Section A',
            instruction='',
            marks_allocation=5,
            questions=SimpleNamespace(all=lambda: [question]),
        )
        exam = SimpleNamespace(
            scoring_enabled=False,
            sections=SimpleNamespace(all=lambda: [section]),
        )

        context = export_exam_to_pdf_html(exam, include_marks=True)

        self.assertFalse(context['include_marks'])
        self.assertIsNone(context['sections'][0]['marks_allocation'])
        self.assertIsNone(context['sections'][0]['questions'][0]['marks'])

    def test_import_endpoint_returns_sections_for_approved_teacher(self):
        request = RequestFactory().post(
            '/exams/exam-papers/import-document/',
            {
                'document': SimpleUploadedFile(
                    'paper.docx',
                    make_docx().getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                ),
                'mode': 'editable_questions',
            },
        )
        request.user = SimpleNamespace(is_authenticated=True, teacher_profile=object())

        with patch('exams.views.user_profile_approved', return_value=True):
            response = ExamPaperImportView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['sections'][0]['section_type'], 'objective')

    def test_editable_import_parses_questions_and_options(self):
        sections = import_docx(make_docx(), 'editable_questions')

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['title'], 'Multiple Choice')
        self.assertEqual(sections[0]['section_type'], 'objective')
        self.assertEqual(sections[0]['questions'][0]['question_text'], '<p>Which colour is shown?</p>')
        self.assertEqual(
            sections[0]['questions'][0]['options'],
            [
                {'option_label': 'A', 'option_text': 'Blue'},
                {'option_label': 'B', 'option_text': 'Green'},
            ],
        )

    def test_preserve_import_keeps_document_content_and_embedded_images(self):
        document = Document()
        document.add_paragraph('Identify this picture:')
        image_buffer = BytesIO()
        Image.new('RGB', (12, 12), color='blue').save(image_buffer, format='PNG')
        image_buffer.seek(0)
        document.add_picture(image_buffer)
        docx_buffer = BytesIO()
        document.save(docx_buffer)
        docx_buffer.seek(0)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                sections = import_docx(docx_buffer, 'preserve_document')

        question_html = sections[0]['questions'][0]['question_text']
        self.assertIn('Identify this picture:', question_html)
        self.assertIn('<img src="/media/exam_resources/', question_html)

    def test_rejects_invalid_document_and_mode(self):
        with self.assertRaisesMessage(ValueError, 'valid .docx'):
            import_docx(BytesIO(b'not a Word file'), 'preserve_document')
        with self.assertRaisesMessage(ValueError, 'valid Word import mode'):
            import_docx(make_docx(), 'unknown')
