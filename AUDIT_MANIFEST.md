# AUDIT_MANIFEST.md — Source Inventory & Code Forensics Manifest

This document provides a complete inventory of source files, categorized counts, and forensic findings across the **BioNEET Pro** codebase.

---

## 1. Inventory Summary

* **Total Active Project Files (excluding .venv, caches, archives):** 1,288 files
* **Primary Source Code Files:** 91 files
* **Core Data & Index Assets:** 1,170 files (including 1,094 sample student profiles and 774 textbook chunks)
* **Active Languages:** Python (90 files), HTML/JavaScript (1 primary file, 4,922 lines), JSON (1,161 files), Markdown (8 files), CSV (5 files)

---

## 2. File Categorization

### Frontend Files (1 file, 4,922 lines)
* `BioNeet-Pro.html` — Primary single-page client interface incorporating HTML structure, CSS custom styling, MathJax, Chart.js, and ES6 module logic.

### Backend Application Files (37 files)
* `app.py` — Main Flask web service and endpoint definitions.
* `adaptive_tutor.py` — Central AI tutor orchestrator and prompt assembler.
* `content_classifier.py` — Query classification engine (in-syllabus, out-of-syllabus, adversarial).
* `policy_engine.py` — Guardrail evaluator and boundary enforcer.
* `syllabus.py` — 32-chapter NCERT Biology validator.
* `concept_graph.py` — Directed acyclic graph of biological concepts.
* `concept_normalizer.py` — Synonym and medical terminology mapping module.
* `nlp_pipeline.py` — Multi-turn pronoun and anaphora resolution pipeline.
* `retrieval_engine.py` — Dual-corpus hybrid TF-IDF retriever.
* `response_validator.py` — Factual faithfulness and NCERT citation verification filter.
* `fallback_controller.py` — Deterministic offline NCERT-grounded doubt solver.
* `learner_model.py` — Bayesian Knowledge Tracing (BKT) and student mastery engine.
* `mcq_engine.py` — Dynamic question generator and evaluation engine.
* `mcq_bank_generator.py` — Bloom-taxonomy-tagged NCERT question generator.
* `score_predictor.py` — Predictive model for estimated NEET score (0–360).
* `flashcard_backend.py` — Leitner / SM-2 spaced repetition flashcard scheduler.
* `firestore_store.py` — Dual-mode persistence abstraction (Firestore + local JSON).
* `ncert_ingestion.py` — PyMuPDF textbook PDF ingestion and chunking pipeline.
* `figure_extractor.py` — Diagrams, figures, and tables extractor from NCERT PDFs.
* `knowledge_ingestion.py` — Knowledge base CSV ingestion utility.
* `dialogue_state.py` — Conversation state and memory tracker.
* `tutor_engine.py` — Supplementary tutor formatting utilities.
* `add_data_1.py`, `add_data_2.py`, `add_data_3.py`, `add_data_4.py` — Knowledge base data seeding routines.
* `fix_data.py`, `update.py`, `update_kb.py` — Knowledge base maintenance utilities.
* `live_battery.py`, `run_e2e_http.py`, `run_big_suite.py`, `run_hostile.py`, `run_sweep.py` — Live API diagnostic runners.
* `verify_bioneetpro_metrics.py`, `verify_fixes.py` — Metric verification utilities.

### Database & Schema Files (4 files)
* `firestore.rules` — Production Cloud Firestore security rules with role-based access control.
* `firestore.indexes.json` — Composite Firestore index specifications.
* `firestore_store.py` — Persistence abstraction layer.
* `data/mcq_firestore_seed.json` — Firestore seed collection for MCQs (4.1 MB).

### Configuration Files (8 files)
* `.env.example` — Environment variable specification template.
* `serviceAccount.json.example` — Firebase service account credentials template.
* `requirements.txt` — Python dependencies specification.
* `Dockerfile` — Docker container specification.
* `firebase.json` — Firebase project and deployment configuration.
* `.firebaserc` — Firebase project binding.
* `.gitignore` — Version control ignore rules.
* `.vscode/settings.json` — IDE editor configuration.

### Test & Benchmark Files (36 files)
* `evaluate_tutor_beast.py` — 98-case golden evaluation suite.
* `evaluate_tutor_system.py` — Full evaluation benchmark runner.
* `test_master_suite.py` — 8-pillar master architectural test suite (17 tests).
* `test_app_endpoints.py` — Flask REST API endpoint tests (5 tests).
* `test_tutor_engine.py` — Tutor engine unit tests (6 tests).
* `test_guardrails.py`, `test_guardrails_integration.py` — Guardrail and safety tests.
* `test_firestore_sync.py`, `test_mastery_sync.py` — Persistence and synchronization tests.
* `test_admin_persistence.py` — Admin role and profile persistence tests.
* `test_safety_hardening.py`, `test_injection_gate.py` — Prompt injection tests.
* `test_syllabus_boundary.py`, `test_syllabus_edge_cases.py` — Boundary validation tests.
* `test_mcq_chapter_purity.py`, `test_mcq_words.py` — Question engine purity tests.
* `test_flashcard_flow.py` — Flashcard SM-2 review flow tests.
* `benchmark/run_classifier_eval.py` — Classification benchmark evaluator.
* `benchmark/keyword_baseline.py` — Keyword baseline comparator.
* `benchmark/adversarial_dataset.json` — Benchmark adversarial test set.
* `benchmark/classifier_dataset.json` — Benchmark classification test set.
* `tests/golden_tutor.json` — Golden reference query-response pairs.

### Documentation Files (11 files)
* `README.md` — Original project overview.
* `IMPLEMENTATION_REPORT.md` — Exhaustive implementation report.
* `CHAPTER_RECONCILIATION.md` — NCERT rationalization audit.
* `first_review_prep_guide.md` — Project review prep notes.
* `review_day_cheat_sheet.md` — Quick cheat sheet.
* `evaluation_report.md` — System evaluation results summary.
* `AUDIT_README.md` — Comprehensive architecture and audit map.
* `PROJECT_STRUCTURE.md` — Codebase structural hierarchy.
* `DEPLOYMENT_NOTES.md` — Deployment and operations guide.
* `AUDIT_MANIFEST.md` — This file.
* `AUDIT_FINDINGS.md` — Detailed findings and risk analysis.

---

## 3. Suspicious and Problematic Code Catalog

### TODO / FIXME Comments
* **Count:** 0
* *Result:* No unresolved TODO or FIXME markers detected across active source files.

### Hardcoded Localhost / Loopback URL References (14 Occurrences)
| File | Line | Snippet | Severity |
|---|---|---|---|
| `app.py` | 45 | `http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173...` | INFO (CORS default) |
| `BioNeet-Pro.html` | 1500 | `const AI_BACKEND_URL = window.BIONEET_AI_BACKEND_URL || "http://127.0.0.1:5000";` | HIGH (Prod fallback) |
| `BioNeet-Pro.html` | 3455 | `'...start the backend (python app.py on http://127.0.0.1:5000)...'` | MEDIUM (Hardcoded user tip) |
| `.env.example` | 12 | `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173...` | INFO (Example config) |
| `live_battery.py` | 6 | `BASE = "http://127.0.0.1:5000"` | INFO (Test harness) |
| `run_e2e_http.py` | 5 | `BASE = "http://127.0.0.1:5000"` | INFO (Test harness) |
| `README.md` | 10 | `Talks to the backend at http://127.0.0.1:5000` | INFO (Docs) |
| `first_review_prep_guide.md` | 33, 49 | `http://127.0.0.1:5000` | INFO (Docs) |

### Console.log Calls in Frontend (32 Occurrences)
* `BioNeet-Pro.html` contains 32 `console.log` statements in client initialization, Firebase syncing, and test submission logic (e.g. lines 4603, 4613, 4657, 4681, 4719, 4752, 4855).  
  *Impact:* Low risk; logs verbose status to browser console.

### Character Encoding: Non-Printable UTF-8 BOM
* Four Python source files begin with the UTF-8 Byte Order Mark (`\ufeff`):
  1. `content_classifier.py`
  2. `policy_engine.py`
  3. `response_validator.py`
  4. `test_guardrails.py`  
  *Impact:* Python 3 handles UTF-8 BOM natively when opening via standard mechanisms, but some external AST parsers or linters (not using `utf-8-sig`) throw `SyntaxError: invalid non-printable character U+FEFF`.

### Credentials Detected in Original Repository
1. `.env.local`: Contains an active OpenRouter API key.  
   *Remediation:* Excluded from the audit package; placeholder provided in `.env.example`.
2. `serviceAccount.json`: Contains an active Google Cloud service account private RSA key.  
   *Remediation:* Excluded from the audit package; sanitized template provided in `serviceAccount.json.example`.

### Final Hardening Sprint — Inventory Delta (2026-09-05)
* MCQ bank: `data/mcq_firestore_seed.json` 6553 -> **6600** unique valid
  (33/33 chapters >= 200, 0 duplicates); engine pool identical.
* New: `scripts/verify_mcq_coverage.py`, `tests/test_security_regression.py`
  (11 tests), `tests/test_markdown_rendering.py` (5 tests), `MCQ_COVERAGE_REPORT.*`,
  `MCQ_QUALITY_REPORT.md`, `API_ACCESS_CONTROL.md`, `BASELINE_VERIFICATION.md`,
  `STALE_FILES_REPORT.md`, `FINAL_VERIFICATION_REPORT.md`.
* Changed: `app.py` (auth/admin/validation/health), `mcq_bank_generator.py`
  (dedupe blind-spot fixes + full-cache seed), `Dockerfile` (full copy +
  gunicorn), `requirements.txt` (+gunicorn), `BioNeet-Pro.html` (same-origin
  backend default, ID-token attach, list-`<br>` fix), `.env.example` (new flags),
  `test_app_endpoints.py` (tracker test -> admin-protection assertion).
* Localhost HIGH item (`BioNeet-Pro.html:1500` bare localhost default) RESOLVED;
  remaining localhost strings are dev/test-harness/docs only.
