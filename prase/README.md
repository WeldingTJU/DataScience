# **prase** – Publisher-agnostic HTML/XML parsing toolkit
*A lightweight toolbox that batch-converts journal HTML/XML files into plain-text, JSON and Markdown tables.*

---

## 📦 Directory layout

```text
prase/
├── html_mdpi_prase.py          # MDPI journals
├── html_springer_prase.py      # Springer Nature
├── html_parse_wiley.py         # Wiley Online Library
├── html_parse_sage.py          # SAGE Journals
├── html_parse_taylorfranics.py # Taylor & Francis
├── html_parse_asme.py          # ASME Digital Collection
├── html_parse_iop.py           # IOPscience
├── html_table_parse.py         # generic HTML-table extractor
├── xml_prase.py                # Elsevier JATS-XML full text
├── xml_table_prase.py          # Elsevier XML tables
└── README.md                   # this guide
```

---

## 🎯 What it does

| Feature              | Details                                                                                               |
|----------------------|-------------------------------------------------------------------------------------------------------|
| **Full-text parsing**| Extract title, abstract, keywords, hierarchical headings and paragraphs                                |
| **Table parsing**    | Return clean JSON plus Markdown preview, handling `rowspan` / `colspan`                               |
| **Logging**          | Auto-creates `parse.log` to spot any failed file instantly                                             |

---

## 🚀 Quick start

```bash
# 1. install dependencies (Python ≥ 3.8)
pip install \
  beautifulsoup4>=4.11.2 \
  lxml>=4.9.3 \
  pandas>=1.5.3 \
  requests>=2.31.0 \
  chardet>=5.2.0 \
  prettytable>=3.9.0

# 2. drop raw HTML files in the corresponding folder
python html_springer_prase.py   # edit ROOT path inside the script
```

### Output snapshot

```text
html/springer/
├── 10.1007_s40194-023-01488-5.html      # raw input
├── 10.1007_s40194-023-01488-5.txt       # plain text
├── json/
│   └── 10.1007_s40194-023-01488-5.json  # structured JSON
└── parse.log                            # runtime log
```

When tables are present you’ll also get:

```text
html/springer/
├── data_table.json   # all tables as JSON
└── data_table.md.txt # Markdown preview
```

Happy parsing 🎉
