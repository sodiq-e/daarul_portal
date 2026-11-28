# FreeDict English–Arabic dictionary data

The bundled lookup data is converted from the FreeDict Eng–Ara TEI source at
commit `5bdceeac8d0dba3298c1bebe734f60d54dad30f7`. The compressed TEI source,
contributor list, and full GPL-2.0 license are included under
`static/data/freedict/`.

The generated browser data combines these translations with English meanings
from Princeton WordNet 3.0. Both sources and their licenses are included under
`static/data/`.

Rebuild it with:

```text
python scripts/build_english_arabic_dictionary.py static/data/freedict/english-arabic.tei.gz static/data/wordnet/wordnet-3.0.zip static/data/english-arabic-dictionary-v2.json
```
