# PART 3 — Textbook forensic audit

Location: `Textbook/` — 34 PDFs, **504 pages**, all text-readable (min-chars check passed, 0 unreadable).
19 Class XI (`kebo101–119`), 13 Class XII (`lebo101–113`), 2 prelims (`kebo1ps`, `lebo1ps`).
Full per-file table: `textbook_inventory.json` (filename, pages, chars, image count, detected class/chapter).

## Pipeline trace (`ncert_ingestion.py` → `data/ncert_textbook_index.json`, 774 chunks)

| Stage | Verdict | Evidence |
|---|---|---|
| EXTRACTION (PyMuPDF page text) | IMPLEMENTED | `process_chapter_pdf` (line 236); all 34 PDFs re-harvested to 573 captions/25 tables/178 exercises by `figure_extractor.py` |
| CLEANING (headers/footers/reprint/hyphenation) | IMPLEMENTED | `clean_page_text` (150), `get_actual_page_number` (123) |
| CHAPTER DETECTION (filename `kebo/lebo` + TOC prelims) | IMPLEMENTED | `_load_tocs` (59), regex `[a-z]+1(\d{2})` (249) |
| SECTION DETECTION (`8.1`, `8.5.4` heading regex) | IMPLEMENTED | `sec_pattern` (291); inventory shows real sections (e.g. `8.5.4 Mitochondria`, `18.4.3 Hindbrain`) |
| CHUNKING (~200-word section-respecting blocks, ≥35 words) | IMPLEMENTED | `flush_chunk` (259), 774 chunks committed |
| METADATA (chunk_id/class/chapter/section/page/file) | IMPLEMENTED | chunk dict (274–287); 12-key schema verified in index |
| CONCEPT EXTRACTION (suffix heuristics + known-concept list) | PARTIALLY IMPLEMENTED | `extract_keywords_and_concepts` (177): misses real terms — live proof: 5 earthworm chunks had `concepts: []`; earthworm/pherenima absent from `known_concepts` until patched |
| INDEXING (`ncert_textbook_index.json` + checksum cache) | IMPLEMENTED | `build_and_save_index` (339); checksums file present |
| RETRIEVAL USE AT RUNTIME | IMPLEMENTED | `retrieval_engine._retrieve_textbook_candidates` (266) + `_single_search`; textbook titles observed live (e.g. `8.5.4 Mitochondria`, `12.2 GLYCOLYSIS`, `4.2.6 Phylum Annelida`) |
| IMAGE/FIGURE USE AT RUNTIME | PARTIALLY IMPLEMENTED | Captions indexed (573) and attached to results (`_attach_figures_tables`); PNG dump skipped (`--fast`); frontend renders caption hints only |

## Gaps found

1. Rationalization gap: `lebo112.pdf` (Ecosystem) contains **0 mentions** of succession/xerarch (verified by direct PDF grep) — content was removed from current NCERT, yet syllabus lists related keywords. A supplementary KB row (`BIO-C36-02`) covers it, labeled as such.
2. Concept extractor blind spots force reliance on hand aliases (see root-cause file).
