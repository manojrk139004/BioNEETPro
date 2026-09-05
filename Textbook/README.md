# Textbook / NCERT Biology PDFs

This directory holds the 34 official NCERT Biology textbook PDFs for Class 11 and Class 12:
- **19 Class 11 Chapters:** `kebo101.pdf` through `kebo119.pdf` + `kebo1ps.pdf` (Prelims)
- **13 Class 12 Chapters:** `lebo101.pdf` through `lebo113.pdf` + `lebo1ps.pdf` (Prelims)

### Ingestion & Chunking
The text and section structure of these textbooks have been extracted and indexed into:
`data/ncert_textbook_index.json` (774 section-aligned chunks).

The raw binary PDFs (~218 MB) are excluded from the lightweight audit ZIP distribution to keep the package within AI reviewer file limits. The full extraction logic is available in `ncert_ingestion.py` and `figure_extractor.py`.
