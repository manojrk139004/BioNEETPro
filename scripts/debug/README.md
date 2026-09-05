# Debug / scratch archive (moved from repo root, Phase 11 hygiene)

These files were sitting at the repo root and are NOT part of any test suite.
Nothing was deleted — moved here intact on 2026-09-04 so `test_*.py` discovery
at root only finds real suites.

- `test_debug*.py`, `test_retrieval_debug*.py`, `test_search_debug.py` — one-off
  debug scripts (use `scripts/test_retrieval_quick.py` for quick checks instead).
- `test_*.txt` — captured chat/lesson/quiz transcripts from manual sessions.
- `check_*.py` — one-off data sanity scripts.
- `verify_key_match.py` — one-off key check (not a suite; the real post-change
  suite is `verify_fixes.py` at root, which stays).

Real suites that stay at root / `tests/`: `test_master_suite.py`,
`test_app_endpoints.py`, `test_tutor_engine.py`, `test_guardrails.py`,
`test_safety_hardening.py`, `test_mcq_chapter_purity.py`, `verify_fixes.py`,
everything under `tests/` and `scripts/test_*acceptance*.py`.
