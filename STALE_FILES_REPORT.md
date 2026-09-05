# STALE_FILES_REPORT.md — Duplicate / Stale File Audit (2026-09-05)

## Verdict: NO files deleted. Root utilities intentionally kept.

Every candidate below was checked for live references before deciding.

### Root one-shot / eval scripts — KEPT (referenced by docs & workflows)
- `add_data_1..4.py`, `fix_data.py`, `update.py`, `update_kb.py` — one-shot KB
  patches; listed in `AUDIT_MANIFEST.md` and `PROJECT_STRUCTURE.md`. Not imported
  by `app.py`, but documented manual-maintenance utilities. Moving them would
  break documented paths. KEPT at root.
- `run_sweep.py`, `run_hostile.py`, `run_e2e_http.py`, `run_big_suite.py`,
  `live_battery.py`, `evaluate_tutor_beast.py`, `evaluate_tutor_system.py`,
  `verify_fixes.py`, `verify_bioneetpro_metrics.py` — eval/diagnostic runners
  referenced by `README.md`, `IMPLEMENTATION_REPORT.md`, `AUDIT_MANIFEST.md`.
  KEPT at root.
- `scripts/debug/README.md` explicitly notes `verify_fixes.py` stays at root.

### Legacy duplicates — STALE but retained on disk, EXCLUDED from audit ZIP
- `archive/legacy_frontend/` (auth.js, config.js, styles.css, utils.js) — superseded
  by the single-file `BioNeet-Pro.html` (live). Not referenced by app code.
- `archive/datasets/` (~170 MB CSVs incl. train1.csv 125 MB) — superseded by
  `datasets/test1.csv` used by `mcq_engine.py`. Not referenced.
- Root `BioNeetPro*.zip` / `BioNEETPro*.zip` (~1.4 GB total across 9 archives) —
  prior build/audit snapshots, gitignored (`BioNeetPro*.zip`). Not deleted (owner
  artifacts); excluded from the rebuilt audit ZIP.
- `AUDIT_2026-09-03_BioNEETPro/` + `AUDIT_2026-09-03_BioNEETPro.zip` — previous
  audit snapshot incl. its own `10_source/` copy of the frontend; historical,
  excluded from the new ZIP.
- `data/indexed_mcqs_cache.pre_dedupe.json` — pre-dedupe backup created by this
  sprint as rollback evidence. Kept on disk; excluded from ZIP (derivable).

### Secrets — NEVER in repo distribution
- `serviceAccount.json`, `.env`, `.env.local` — gitignored, live on dev machine
  only, excluded from the audit ZIP. Only `.env.example` (names, no values) ships.
