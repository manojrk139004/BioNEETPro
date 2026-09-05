# PART 16/18 — Methodology + package guide

Method: dynamic discovery (no filename assumptions beyond root + `Textbook/`) →
SHA256 preservation manifest of 156 files → byte-identical source copies (integrity re-verified) →
per-PDF text/image/quality scan → dataset schema + code-reference grep (production vs dormant) →
threshold/weight/intent/model facts pinned to file:line → 36 live probes via production code paths
(`adaptive_tutor`, `mcq_engine`, `nlp_pipeline`, `learner_model`) with `.env.local` loaded so the
measured path equals the deployed path → probe artifacts removed + append-only logs truncated to
baseline bytes (tracker 38628, querylog 2368; counts re-verified: 271 lines / 8 lines / 43 profiles /
3 dialogues) → docs → zip.

## Package contents

- `00_preservation_manifest.csv` — SHA256 of all 156 project files (re-hash to verify untouched)
- `10_source/` — complete byte-identical sources (backend .py, `BioNeet-Pro.html`, `js/`, tests, scripts, configs)
- `textbook_inventory.json` — 34 PDFs: pages/chars/images/class/chapter/readability
- `dataset_inventory_data.json`, `dataset_inventory_datasets.json` — schemas, row counts, samples
- `01_project_inventory.md`, `02_environment.md`
- `20_textbook_audit.md` (11-stage pipeline verdicts), `21_dataset_audit.md` (wiring table)
- `22_retrieval_nlp_forensics.md` (formula, thresholds, intents), `23_context_learner_mcq_api_forensics.md`
- `40_probe.py` (re-runnable probe), `41_runtime_results.jsonl` (raw), `30_runtime_results.md` (table)
- `31_requirement_matrix.md`, `32_root_cause.md`, this file

Excluded per spec: `.venv/`, `__pycache__/`, build output, secrets (`[REDACTED]`), old `*.zip` snapshots.
Note: `40_probe.py` appends runtime state when executed — clean `forensic_probe*` artifacts after re-runs.
