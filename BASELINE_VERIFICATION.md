# BASELINE_VERIFICATION.md — Pre-Change Baseline (2026-09-05)

Recorded BEFORE any hardening-sprint modification. All values observed directly.

## Inventory
- Total files (recursive, incl. .venv/caches/archives on disk): ~1560 entries.
- Frontend: `BioNeet-Pro.html` (269,608 bytes, 4921 lines).
- Backend: `app.py` (1188 lines), 20+ engine modules.
- MCQ bank: `data/mcq_firestore_seed.json` = **6553** records across **33** chapters
  (22 chapters below 200; lowest Plant Growth and Development = 183).
  Engine pool `data/indexed_mcqs_cache.json` = **6710** records (all 33 >= 200,
  but containing 778 exact duplicates — found later during verification).
- Textbook: `Textbook/` present with 35 PDFs (kebo1xx/lebo1xx).

## Test baseline (all PASS before changes)
- `test_master_suite.py`: 17 tests OK
- `test_app_endpoints.py`: 5 tests OK
- `test_guardrails.py`: 12 tests OK
- `test_tutor_engine.py`: 6 tests OK

## Behavior baseline
- Build: no build step (static HTML + Flask). `python -c "import app"` OK.
- Lint/type-check: not configured in repo (no ruff/mypy config) — N/A.
- Firebase connectivity: `firestore_store.status()` = enabled (serviceAccount.json
  valid on this machine). Secrets on disk are gitignored, excluded from audit ZIPs.
- API health: `GET /health` returns status ok (verified via test client).
- Auth: backend trusted body/query `student_id` with no token verification
  (`auth_student_id` accepted raw Bearer uid) — recorded as AUTH-01, fixed in sprint.
- Admin: `/api/mcqs/generate`, `/api/tutor/import-kaggle`, `/api/tutor/tracker`
  callable without admin proof — recorded, fixed in sprint.
- Tutor: local-first RAG answers via `/chat`, `/ask`, `/api/tutor/answer` — working.
- Markdown: `formatAIReply()` escape-first + limited tags (headings/bold/italic/
  lists/code/citations/safe links) — working, kept and regression-tested.
