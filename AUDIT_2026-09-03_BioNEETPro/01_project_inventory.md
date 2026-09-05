# PART 1 — Project Inventory (discovered dynamically, 2026-09-03)

Root: `BioNeetPro (1)/` — NOT a git repo. Python 3.13.7. 156 files hashed (see `00_preservation_manifest.csv`).

## Directories

| Directory | Contents | Role |
|---|---|---|
| `Textbook/` | 34 PDFs, 504 pages, all text-readable | Production textbook source (19× Class XI `kebo101–119`, 13× Class XII `lebo101–113`, 2 prelims `kebo1ps/lebo1ps`) |
| `data/` | 10 data files + `dialogue_states/` (3) + `kaggle_imports/` (1) + `student_profiles/` (43) | Production data + runtime learner state |
| `datasets/` | 9 CSVs (8767 … 182822 rows; train1.csv 122 MB) | Dormant — only `test1.csv` referenced in code |
| `tests/` | 4 unittest files + `golden_tutor.json` (98 cases) + `gate_results.jsonl` | Test/evaluation data |
| `scripts/` | `import_kaggle_dataset.py` + 4 acceptance/quick-test scripts | Tooling + extra tests |
| `js/` (`auth.js`, `config.js`, `utils.js`), `css/` (`styles.css`) | Legacy frontend fragments | ORPHANS — zero references from `BioNeet-Pro.html` (verified by grep) |
| `BioNeet-Pro.html` (4275 lines, 256 KB, 1 script tag) | Single-file frontend (Firebase CDN + backend at `127.0.0.1:5000`) | Production frontend |
| `.venv/`, `__pycache__/` | Dependencies, bytecode | Excluded from audit |
| `*.zip` (4 files, 64–406 MB) | Old snapshots | Archives, not source |

## Backend source files (all imported at runtime unless noted)

| File | Purpose | Imported by | Affects tutor |
|---|---|---|---|
| `app.py` | Flask app, all routes, rate limit, unified answer builder | executed directly | YES |
| `adaptive_tutor.py` | ONE generator: RAG over evidence pack + template fallback | `app.py` | YES |
| `retrieval_engine.py` | Dual-corpus hybrid retrieval + rerank + compare-split | `app.py` (via tutors), `tutor_engine.py`, `adaptive_tutor.py` | YES |
| `nlp_pipeline.py` | Shorthand/typo normalize, anaphora, intent, Bloom, entities, syllabus gate | tutors, `app.py` | YES |
| `concept_normalizer.py` | ~260 alias → canonical mappings + typo map + dynamic index load | `nlp_pipeline.py`, `retrieval_engine.py`, `mcq_engine.py`, `adaptive_tutor.py` | YES |
| `syllabus.py` | 33-chapter registry, keyword/generic/rarity-fallback gate | `nlp_pipeline.py`, `app.py`, ingestion | YES |
| `concept_graph.py` | 115 nodes / 97 edges, BFS/neighbors/prereqs/causal/contrast | retrieval (+0.05), `tutor_engine.py`, `adaptive_tutor.py` | PARTIAL |
| `tutor_engine.py` | 4-step Socratic sessions + BKT + CSV tracker | `app.py` (step endpoints) | YES (step mode) |
| `learner_model.py` | BKT profiles (JSON per student), weak topics, trajectory | `app.py`, tutors, `mcq_engine.py` | YES |
| `mcq_engine.py` | Parse/generate/validate/format MCQs, pool from KB + test1.csv | `app.py`, `adaptive_tutor.py` (NOT used — chat path only) | YES (chat path) |
| `fallback_controller.py` | Feature-flagged emergency API fallback (`ENABLE_API_FALLBACK=false` default) | `app.py` | On LOW only |
| `dialogue_state.py` | Persistent turns/focal + FSRS-lite review schedule | `app.py` | YES (metadata) |
| `knowledge_ingestion.py` | KB validation/append/dedupe + coverage report | manual/scripts | Data pipeline |
| `ncert_ingestion.py` | PDF → chunks pipeline (PyMuPDF) | manual/first-run | Data pipeline |
| `figure_extractor.py` | Captions/tables/exercises harvest | manual (indexes committed) | Data pipeline |
| `update_kb.py`, `update.py`, `fix_data.py`, `add_data_1–4.py` | One-off data maintenance scripts | manual | Historical |
| `scripts/import_kaggle_dataset.py` | `data/kaggle_imports/` → KB via `/api/tutor/import-kaggle` | `app.py` (lazy import) | On demand |
| `evaluate_tutor_beast.py` + `tests/golden_tutor.json` | 98-case gate (see `tests/gate_results.jsonl`) | manual | Evaluation |
| `evaluate_tutor_system.py` | Older system evaluator | manual | Historical |
| `test_*.py` (root, 3 files), `tests/test_*.py` (4 files), `scripts/test_*.py` (4 files) | unittest suites | manual/CI | Regression |

## Config

`requirements.txt` (Flask 3.1.2, flask-cors 6.0.1, pandas 3.0.3, scikit-learn 1.9, pymupdf 1.28.2, python-dotenv 1.2.1, requests 2.32.5),
`Dockerfile` (backend-only, port 5000), `firestore.rules`, `firestore.indexes.json`,
`.env.example` (placeholders), `.env.local` (live secrets — REDACTED in this package; keys present: `OPENROUTER_API_KEY=[REDACTED]`, model `agnes-2.0-flash`, `ALLOWED_ORIGINS` localhost/5173/5500/5000).
