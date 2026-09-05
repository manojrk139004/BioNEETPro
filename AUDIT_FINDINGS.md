# AUDIT_FINDINGS.md — Technical Vulnerability, Bug & Deployment Risk Report

This report catalogs all identified bugs, architectural risks, security concerns, and deployment blockers discovered during the inspection of **BioNEET Pro**. In accordance with audit standards, no source code has been altered.

---

## 1. Executive Summary Table

| ID | Title | Category | Severity | Location |
|---|---|---|---|---|
| **SEC-01** | Real OpenRouter Secret API Key in `.env.local` | Security | **CRITICAL** | `.env.local:1` |
| **SEC-02** | Real Firebase Private Key in `serviceAccount.json` | Security | **CRITICAL** | `serviceAccount.json:5` |
| **DEP-01** | Incomplete Dockerfile `COPY` Instruction | Deployment | **HIGH** | `Dockerfile:15` |
| **DEP-02** | Hardcoded Localhost Fallback in Client | Deployment / Networking | **HIGH** | `BioNeet-Pro.html:1500` |
| **AUTH-01**| Backend Endpoints Lack JWT Verification | Security / Authorization | **HIGH** | `app.py` |
| **DEP-03** | In-Memory State Unsynchronized in Multi-Worker Deployment | Architecture | **MEDIUM** | `app.py:60,90` |
| **ENC-01** | UTF-8 Byte Order Mark (BOM) in Core Modules | Code Quality | **MEDIUM** | `content_classifier.py`, etc. |
| **SEC-03** | Public Cloud Read on MCQs Collection | Security | **LOW** | `firestore.rules:49` |
| **LOG-01** | Verbose `console.log` Logging in Production Client | Code Quality | **LOW** | `BioNeet-Pro.html` (32 instances) |
| **DEP-04** | Flask Development Server Invoked in Docker CMD | Deployment | **LOW** | `Dockerfile:25` |

---

## 2. Detailed Findings

### [CRITICAL] SEC-01: Secret API Key Stored in `.env.local`
* **File:** `.env.local` (line 1)
* **Description:** The local environment file contains an active OpenRouter API key (`sk-nry-[REDACTED_API_KEY]`).
* **Risk:** Anyone gaining access to the file or committing it to a public repository can consume the project owner's LLM credits or abuse the API.
* **Audit Action:** Excluded `.env.local` from the audit distribution archive. Documented variable in `.env.example`. Project owner should immediately rotate this key in OpenRouter console.

---

### [CRITICAL] SEC-02: Firebase Service Account Private Key in Repository
* **File:** `serviceAccount.json` (line 5)
* **Description:** A full Google Cloud service account JSON credentials file with private RSA key block (`[RSA_PRIVATE_KEY_BLOCK]`) is present in the project root.
* **Risk:** Grants administrative access to the `bioneet-pro-a73d5` Firebase project, allowing unrestricted reads and writes to all Firestore collections, user data, and authentication records.
* **Audit Action:** Excluded `serviceAccount.json` from the audit distribution archive. Provided sanitized `serviceAccount.json.example`. Project owner should revoke and regenerate this key in Google Cloud Console.

---

### [HIGH] DEP-01: Incomplete Dockerfile `COPY` Instruction
* **File:** `Dockerfile` (line 15)
* **Description:** The Dockerfile contains:
  ```dockerfile
  COPY app.py app.py
  ```
  It does not copy the required Python modules (`adaptive_tutor.py`, `retrieval_engine.py`, `syllabus.py`, `content_classifier.py`, `policy_engine.py`, `firestore_store.py`, etc.) nor does it copy the `data/` directory.
* **Risk:** Running `docker build` and `docker run` will cause the container to fail on startup with:
  ```text
  ModuleNotFoundError: No module named 'adaptive_tutor'
  ```
* **Remediation Note:** Change line 15 to `COPY . /app` or explicitly copy all application modules and data assets.

---

### [HIGH] DEP-02: Hardcoded Localhost URL Fallbacks in Client
* **File:** `BioNeet-Pro.html` (lines 1500, 3455)
* **Description:** Line 1500 defines:
  ```javascript
  const AI_BACKEND_URL = window.BIONEET_AI_BACKEND_URL || "http://127.0.0.1:5000";
  ```
  If `window.BIONEET_AI_BACKEND_URL` is not injected by the web server, all requests to the AI tutor, MCQ generator, and score predictor default to `http://127.0.0.1:5000`.
* **Risk:** When deployed to a public domain, client browsers will attempt to connect to the visitor's local machine rather than the deployed backend, resulting in `ERR_CONNECTION_REFUSED`.

---

### [HIGH] AUTH-01: Backend Endpoints Lack Token Verification
* **File:** `app.py`
* **Description:** While `firestore.rules` enforces authorization at the Cloud Firestore database layer, the Flask API endpoints in `app.py` (e.g. `/api/tutor/answer`, `/api/flashcards/review`, `/api/mcq/generate`) accept a `student_id` in the request body or query parameter without validating a Firebase Auth JWT bearer token (`Authorization: Bearer <token>`).
* **Risk:** Any client can submit queries or reviews under arbitrary `student_id` identifiers, potentially polluting student mastery vectors or chat logs.

---

### [MEDIUM] DEP-03: In-Memory State Unsynchronized Across Multi-Worker Deployment
* **File:** `app.py` (lines 60, 90)
* **Description:**
  1. `_rate_buckets` (line 60) tracks IP request frequency in a Python `defaultdict(deque)`.
  2. `_append_chat_turn` (line 90) reads and writes turns locally before Firestore syncing.
* **Risk:** In production deployments using Gunicorn multi-worker models (`-w 4`) or multi-container clusters, rate limits are not shared across workers, effectively multiplying allowable request limits by the number of worker processes.

---

### [MEDIUM] ENC-01: UTF-8 Byte Order Mark (BOM) in Python Files
* **Files:** `content_classifier.py`, `policy_engine.py`, `response_validator.py`, `test_guardrails.py`
* **Description:** These files begin with the 3-byte sequence `EF BB BF` (UTF-8 BOM).
* **Risk:** While standard Python 3.8+ handles UTF-8 BOM, third-party static linters, AST inspectors, or Unix build tools that open files with plain `utf-8` rather than `utf-8-sig` may trigger syntax errors.

---

### [LOW] SEC-03: Public Cloud Read Permission on MCQs Collection
* **File:** `firestore.rules` (line 49)
* **Description:**
  ```text
  match /mcqs/{mcqId} {
    allow read: if true;
  }
  ```
  MCQs are readable by unauthenticated users.
* **Risk:** Allows scraping of the entire question bank. (Note: May be an intentional design choice to enable public practice tests without requiring registration).

---

### [LOW] LOG-01: Verbose `console.log` in Production Client
* **File:** `BioNeet-Pro.html` (32 instances)
* **Description:** Detailed logs regarding MCQ syncing, video updates, and test submissions are written to browser developer tools.
* **Risk:** Exposes internal state variables and sync metrics to end users.

---

### [LOW] DEP-04: Flask Development Server in Dockerfile CMD
* **File:** `Dockerfile` (line 25)
* **Description:** `CMD ["python", "app.py"]` launches the built-in Flask/Werkzeug server.
* **Risk:** Werkzeug is single-threaded by default, not hardened for production traffic, and issues explicit warnings against production use.

---

## 3. Verification & Test Execution Results

All commands were executed against the actual codebase without modifying any source code:

| Command | Status | Result / Output Summary |
|---|---|---|
| `python evaluate_tutor_beast.py` | **PASS** | 98/98 Golden Cases Passed (Bio: 91/91, Out-of-Syllabus: 7/7, Faithfulness: 0.525). Gate: **GREEN - SHIP IT**. |
| `python test_master_suite.py` | **PASS** | Ran 17 tests across all 8 architectural pillars in 10.08s. Result: **OK**. |
| `python test_app_endpoints.py` | **PASS** | Ran 5 endpoint tests in 13.89s. Result: **OK**. |
| `python test_tutor_engine.py` | **PASS** | Ran 6 tutor engine tests in 4.58s. Result: **OK**. |
| `python -m compileall -q .` | **PASS** | Successfully compiled all 90 Python source files. 0 syntax errors. |
| `python -m mypy` | **NOT AVAILABLE** | Type checker not installed in virtual environment. |
| `python -m flake8` | **NOT AVAILABLE** | Linter not installed in virtual environment. |

---

## 4. Final Hardening Sprint — Resolution Appendix (2026-09-05, independently verified)

| ID | Resolution | Evidence |
|---|---|---|
| SEC-01 / SEC-02 | No change to secret handling by design: secrets stay gitignored and are EXCLUDED from the rebuilt audit ZIP. Owner must still rotate keys if ever exposed. | ZIP contents inspected; `.env.example` names-only |
| DEP-01 | Dockerfile now copies all 20 engine modules + data/scripts/datasets; gunicorn CMD | `test_12` PASS; build DEFERRED (no daemon) |
| DEP-02 | Same-origin default + override; token attached on chat | `test_11` PASS |
| AUTH-01 | Real `verify_id_token`; `REQUIRE_FIREBASE_AUTH` strict mode; admin gating; self-only learner data | security_regression 11/11 PASS |
| DEP-03 | Kept (low-volume appropriate); documented; Redis upgrade path noted | `API_ACCESS_CONTROL.md` |
| DEP-04 | CMD is now gunicorn (2 workers, 120s timeout) | `Dockerfile`, `requirements.txt` |
| MCQ-01 (new) | Seed 6553/22-thin + 778 hidden dups resolved: honest dedupe -> 5932 -> topped to 6600 unique, 33/33x200 | verifier exit 0, coverage+quality reports |
