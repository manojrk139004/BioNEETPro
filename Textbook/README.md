# Authoritative NCERT Biology Textbooks Directory

This directory is designated for the official NCERT Class 11 and Class 12 Biology PDF textbooks.

## Chapter Filename Mapping:
- **Class 11 (Chapters 1 to 22)**: kebo101.pdf through kebo122.pdf
- **Class 12 (Chapters 23 to 38)**: kebo201.pdf through kebo216.pdf

## Ingestion & Retrieval:
All 38 textbooks are ingested by 
cert_ingestion.py into data/ncert_textbook_index.json.
At runtime, etrieval_engine.py queries data/ncert_textbook_index.json using TF-IDF and character-level sliding windows for sub-second retrieval.

For size efficiency in source handovers, kebo101.pdf is included as a representative sample demonstrating the document layout, diagrams, and section structure expected by 
cert_ingestion.py.
