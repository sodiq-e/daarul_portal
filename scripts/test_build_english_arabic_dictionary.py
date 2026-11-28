import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from scripts.build_english_arabic_dictionary import convert, read_wordnet_definitions


def write_wordnet_archive(path, noun_data='', noun_index=''):
    with ZipFile(path, 'w') as archive:
        archive.writestr('wordnet/data.noun', noun_data)
        archive.writestr('wordnet/index.noun', noun_index)
        for filename in ('data.verb', 'data.adj', 'data.adv'):
            archive.writestr(f'wordnet/{filename}', '')
        for filename in ('index.verb', 'index.adj', 'index.adv'):
            archive.writestr(f'wordnet/{filename}', '')


class DictionaryBuildTests(unittest.TestCase):
    def test_reads_definitions_from_wordnet_synsets(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / 'wordnet.zip'
            write_wordnet_archive(
                archive_path,
                noun_data='00000001 00 n 01 book 0 0 | a set of written pages; "an example"\n',
                noun_index='book n 1 0 1 1 00000001\n',
            )

            definitions = read_wordnet_definitions(archive_path)

        self.assertEqual(definitions['book'], [['noun', 'a set of written pages']])

    def test_definitions_follow_wordnet_sense_frequency_order(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / 'wordnet.zip'
            write_wordnet_archive(
                archive_path,
                noun_data=(
                    '00000001 00 n 01 bank 0 0 | a less common meaning\n'
                    '00000002 00 n 01 bank 0 0 | a more common meaning\n'
                ),
                noun_index='bank n 2 0 2 2 00000002 00000001\n',
            )

            definitions = read_wordnet_definitions(archive_path)

        self.assertEqual(
            definitions['bank'],
            [['noun', 'a more common meaning'], ['noun', 'a less common meaning']],
        )

    def test_converted_entries_include_available_meanings(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source_path = directory / 'english-arabic.tei'
            source_path.write_text(
                '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
                '<entry><form><orth>Book</orth></form><sense>'
                '<cit type="trans"><quote>الكتاب</quote></cit>'
                '</sense></entry></TEI>',
                encoding='utf-8',
            )
            archive_path = directory / 'wordnet.zip'
            write_wordnet_archive(
                archive_path,
                noun_data='00000001 00 n 01 book 0 0 | a set of written pages\n',
                noun_index='book n 1 0 1 1 00000001\n',
            )
            output_path = directory / 'dictionary.json'

            count = convert(source_path, archive_path, output_path)

            self.assertEqual(count, 1)
            self.assertEqual(
                output_path.read_text(encoding='utf-8'),
                '[["Book",["الكتاب"],[["noun","a set of written pages"]]]]',
            )

    def test_wordnet_entries_without_definitions_remain_translatable(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source_path = directory / 'english-arabic.tei'
            source_path.write_text(
                '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
                '<entry><form><orth>rareword</orth></form><sense>'
                '<cit type="trans"><quote>كلمة نادرة</quote></cit>'
                '</sense></entry></TEI>',
                encoding='utf-8',
            )
            archive_path = directory / 'wordnet.zip'
            write_wordnet_archive(archive_path)
            output_path = directory / 'dictionary.json'

            convert(source_path, archive_path, output_path)
            self.assertEqual(
                output_path.read_text(encoding='utf-8'),
                '[["rareword",["كلمة نادرة"],[]]]',
            )


if __name__ == '__main__':
    unittest.main()
