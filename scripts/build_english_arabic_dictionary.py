import argparse
import gzip
import io
import json
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


TEI_NAMESPACE = '{http://www.tei-c.org/ns/1.0}'
WORDNET_FILES = {
    'wordnet/data.noun': ('noun', 'n'),
    'wordnet/data.verb': ('verb', 'v'),
    'wordnet/data.adj': ('adjective', 'a'),
    'wordnet/data.adv': ('adverb', 'r'),
}
MAX_DEFINITIONS_PER_WORD = 3


def normalize(text):
    return unicodedata.normalize('NFC', text).strip().casefold().replace('_', ' ')


def read_wordnet_definitions(archive_path):
    sense_order = {}
    synsets = {}
    with ZipFile(archive_path) as archive:
        for filename, wordnet_pos in (
            ('wordnet/index.noun', 'n'),
            ('wordnet/index.verb', 'v'),
            ('wordnet/index.adj', 'a'),
            ('wordnet/index.adv', 'r'),
        ):
            with archive.open(filename) as data_file:
                for line in io.TextIOWrapper(data_file, encoding='utf-8'):
                    fields = line.split()
                    if len(fields) < 7 or not fields[0][0].isalpha():
                        continue
                    synset_count = int(fields[2])
                    pointer_count = int(fields[3])
                    first_offset = 4 + pointer_count + 2
                    word = normalize(fields[0])
                    for rank, offset in enumerate(fields[first_offset:first_offset + synset_count]):
                        sense_order[(word, wordnet_pos, offset)] = rank

        for filename, (part_of_speech, wordnet_pos) in WORDNET_FILES.items():
            with archive.open(filename) as data_file:
                for line in io.TextIOWrapper(data_file, encoding='utf-8'):
                    if not line or not line[0].isdigit():
                        continue

                    synset, separator, gloss = line.partition('|')
                    fields = synset.split()
                    if not separator or len(fields) < 4:
                        continue

                    word_count = int(fields[3], 16)
                    words = [
                        fields[index].replace('_', ' ')
                        for index in range(4, 4 + word_count * 2, 2)
                    ]
                    meaning = gloss.split(';', 1)[0].strip().strip('"')
                    if meaning:
                        synsets[(fields[0], wordnet_pos)] = (words, meaning, part_of_speech)

    definitions = {}
    for (offset, wordnet_pos), (words, meaning, part_of_speech) in synsets.items():
        for word in words:
            key = normalize(word)
            word_definitions = definitions.setdefault(key, [])
            definition = [part_of_speech, meaning]
            ranked_definition = (
                sense_order.get((key, wordnet_pos, offset), 10**9),
                wordnet_pos,
                definition,
            )
            if all(item[2] != definition for item in word_definitions):
                word_definitions.append(ranked_definition)

    for key, word_definitions in definitions.items():
        word_definitions.sort(key=lambda item: (item[0], item[1]))
        definitions[key] = [
            item[2] for item in word_definitions[:MAX_DEFINITIONS_PER_WORD]
        ]
    return definitions


def convert(source, wordnet_archive, output):
    definitions = read_wordnet_definitions(wordnet_archive)
    entries = {}
    stack = []

    opener = gzip.open if source.suffix == '.gz' else open
    with opener(source, 'rb') as source_file:
        for event, element in ET.iterparse(source_file, events=('start', 'end')):
            if event == 'start':
                stack.append(element)
                continue

            if element.tag == f'{TEI_NAMESPACE}entry':
                form = element.find(f'{TEI_NAMESPACE}form')
                headword = None
                if form is not None:
                    orthography = form.find(f'{TEI_NAMESPACE}orth')
                    if orthography is not None:
                        headword = ''.join(orthography.itertext()).strip()

                translations = []
                for citation in element.iter(f'{TEI_NAMESPACE}cit'):
                    if citation.get('type') != 'trans':
                        continue
                    for quote in citation.iter(f'{TEI_NAMESPACE}quote'):
                        translation = ' '.join(''.join(quote.itertext()).split())
                        if translation and translation not in translations:
                            translations.append(translation)

                if headword and translations:
                    key = normalize(headword)
                    item = entries.setdefault(key, [headword, [], definitions.get(key, [])])
                    for translation in translations:
                        if translation not in item[1]:
                            item[1].append(translation)

                if len(stack) > 1:
                    stack[-2].remove(element)
                element.clear()

            stack.pop()

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='\n') as dictionary_file:
        json.dump(list(entries.values()), dictionary_file, ensure_ascii=False, separators=(',', ':'))

    return len(entries)


def main():
    parser = argparse.ArgumentParser(description='Build the offline English–Arabic dictionary with meanings.')
    parser.add_argument('source', type=Path)
    parser.add_argument('wordnet_archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    count = convert(args.source, args.wordnet_archive, args.output)
    print(f'Wrote {count} dictionary entries with meanings to {args.output}')


if __name__ == '__main__':
    main()
