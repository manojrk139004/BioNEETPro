# Environment + test commands

- OS: Windows (win32, PowerShell 5.1). Python 3.13.7.
- Installed (relevant): Flask 3.1.2, flask-cors 6.0.1, numpy 2.4.6, pandas 3.0.3,
  pymupdf 1.28.2, python-dotenv 1.2.1, requests 2.32.5, scikit-learn 1.9.0. No pytest (unittest used).
- No `node`, no JS toolchain in project scope (React app was deleted by owner; only static HTML + CDN Firebase 11.0.0 remain).

## How to run (read-only safe)

```bash
python app.py
# then open BioNeet-Pro.html via VS Code Live Server (port 5500), or:
python -c "import app; c=app.app.test_client(); print(c.post('/api/tutor/answer', json={'query':'Why is brain white?'}).get_json().keys())"
```

## Test commands used by this audit

```bash
python test_master_suite.py      # 17 tests
python test_app_endpoints.py     # 5 tests
python test_tutor_engine.py      # 6 tests
python evaluate_tutor_beast.py   # 98-case golden gate (needs network + API key; resumable via tests/gate_results.jsonl)
python AUDIT_2026-09-03_BioNEETPro\40_probe.py   # this audit's 36-probe forensic run -> 41_runtime_results.jsonl
```

Live-test hygiene applied: probe used student_id `forensic_probe[_B]`; afterward the 3 generated
state files were deleted and the 2 append-only logs truncated to baseline bytes
(tracker 38628, query log 2368 — verified). Preservation manifest `00_preservation_manifest.csv`
(SHA256, 156 files) proves zero modification; re-hash to verify.
