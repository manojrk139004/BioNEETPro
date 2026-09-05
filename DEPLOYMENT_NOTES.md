# DEPLOYMENT_NOTES.md — BioNEET Pro Deployment & Production Guide

This document assesses the deployment requirements, environment configurations, operational dependencies, and potential deployment blockers for **BioNEET Pro**, based strictly on the actual codebase implementation.

---

## 1. Framework

* **Frontend:** Vanilla HTML5, CSS3 Custom Properties, and ES6 modules (`BioNeet-Pro.html`). No build step or frontend bundler (e.g., Vite/Webpack/Next.js) is required for execution.
* **Backend:** Python 3.10+ WSGI application powered by Flask 3.1.2 with `flask-cors` 6.0.1.

---

## 2. Build Command

* **Frontend:** None required (pure static files).
* **Backend:**
  ```bash
  pip install -r requirements.txt
  ```

---

## 3. Development Command

To run the application locally in development:

### Step 1: Start Backend
```bash
# Terminal 1: Launch Flask Backend
python app.py
# Server listens on http://127.0.0.1:5000 (or PORT env var)
```

### Step 2: Serve Frontend
```bash
# Terminal 2: Serve HTML with VS Code Live Server or Python HTTP server
python -m http.server 5500
# Open http://127.0.0.1:5500/BioNeet-Pro.html in browser
```

---

## 4. Production Command

### Backend: Production WSGI Server
Do **not** use `python app.py` (Werkzeug development server) in production. Instead, run a production WSGI server such as Gunicorn:
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 app:app
```
*(Note: Worker timeout should be >= 120 seconds to support multi-turn RAG retrieval and LLM generation latency).*

### Frontend: Static CDN Hosting
Deploy `BioNeet-Pro.html` to any static web hosting provider (Cloudflare Pages, Firebase Hosting, Netlify, Vercel, or AWS S3 + CloudFront).

**Production backend URL:** set `window.BIONEET_AI_BACKEND_URL` to the deployed
HTTPS backend before the main script. Since 2026-09-05 the fallback is
same-origin (`window.location.origin`) for http(s) pages — localhost is only the
`file://` dev fallback, so production browsers never call their own machine.

---

## 12. Final Hardening Sprint — Resolution Update (2026-09-05, verified)

| Blocker | Resolution | Evidence |
|---|---|---|
| 1. Incomplete Dockerfile | Fixed: all 20 engine modules + `data/` + `scripts/` + `datasets/` copied; `gunicorn` added to `requirements.txt`; CMD uses gunicorn (2 workers, 120s timeout) | `test_12_docker_contains_required_modules` PASS; image build DEFERRED (no Docker daemon on audit machine) |
| 2. CORS | Unchanged default (dev) — production MUST set `ALLOWED_ORIGINS` | `.env.example` documents |
| 3. Hardcoded localhost | Same-origin default + `window.BIONEET_AI_BACKEND_URL` override + dynamic error message; Firebase ID token attached on chat | `test_11` PASS |
| 4. In-memory limiter | Kept deliberately (low-volume); documented; expensive AI routes (`/chat`, `/ask`, `/api/tutor/answer`) all gated; Redis noted as upgrade | code + `API_ACCESS_CONTROL.md` |
| Auth (AUTH-01) | Real `verify_id_token`, strict mode flag, admin gating, self-only learner data | `tests/test_security_regression.py` 11/11 |
| Health | `GET /api/health` + `GET /api/ready` added | test-client verified |
| Textbook PDFs | `Textbook/` (35 PDFs) present locally; served via map-lookup (traversal-safe); EXCLUDED from audit ZIP by design | `test_13` PASS |

---

## 5. Required Environment Variables

### Backend (`.env` or Server Environment)
| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Recommended | None | Secret API key for OpenRouter LLM gateway. (If absent, backend automatically falls back to offline local NCERT answers). |
| `OPENROUTER_MODEL` | Optional | `openai/gpt-4o-mini` | LLM model identifier. |
| `OPENROUTER_BASE_URL` | Optional | `https://openrouter.ai/api/v1` | Custom gateway endpoint or proxy. |
| `AI_MAX_TOKENS` | Optional | `550` | Maximum token ceiling for AI tutor responses. |
| `ALLOWED_ORIGINS` | Required in Prod | `http://localhost:5000,...` | Comma-separated CORS allowed origins (e.g., `https://bioneetpro.example.com`). |
| `RATE_LIMIT_WINDOW_SECONDS` | Optional | `60` | Duration window for token-bucket rate limiter. |
| `RATE_LIMIT_MAX_REQUESTS` | Optional | `20` | Max requests permitted per IP in window. |
| `FLASK_DEBUG` | Optional | `false` | Flask debug mode flag. |
| `PORT` | Optional | `5000` | Port for Flask web server. |
| `FIREBASE_SERVICE_ACCOUNT` | Optional | `serviceAccount.json` | Path to Firebase service account JSON key. |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Optional | None | Inline JSON string containing service account credentials. |

### Frontend
| Variable / Setting | Required | Default | Description |
|---|---|---|---|
| `window.BIONEET_AI_BACKEND_URL` | Optional | `http://127.0.0.1:5000` | URL of the deployed Flask backend. |
| `firebaseConfig` | Required for Cloud | Pre-configured in HTML | Public Firebase client configuration object. |

---

## 6. Firebase Configuration

1. **Client Configuration (`BioNeet-Pro.html`):**
   * Pre-configured with Firebase Project `bioneet-pro-a73d5`.
   * Client authentication: Email/Password via Firebase Auth.
2. **Server Configuration (`firestore_store.py`):**
   * Uses `firebase-admin` Python SDK.
   * Looks for `FIREBASE_SERVICE_ACCOUNT_JSON` env, `FIREBASE_SERVICE_ACCOUNT` path, or local `serviceAccount.json`.
   * **Graceful Degradation:** If no credentials are found, the backend logs a warning and stores all data as local JSON files under `data/`.
3. **Rules & Indexes:**
   * Rules are specified in `firestore.rules` (enforces role-based permissions for students vs admins).
   * Indexes are defined in `firestore.indexes.json`.
   * Deploy command:
     ```bash
     firebase deploy --only firestore:rules,firestore:indexes
     ```

---

## 7. Backend / API Requirements

* **Python Runtime:** Python 3.10 or higher.
* **Memory Allocation:** Minimum 1 GB RAM (2 GB recommended). The hybrid retrieval engine loads TF-IDF matrices over 774 NCERT chunks into memory on startup.
* **CPU:** 1-2 vCPU cores sufficient for TF-IDF cosine similarity calculations.
* **Disk Storage:** At least 200 MB for data indexes (`data/ncert_textbook_index.json`, `data/neet_knowledge_base.csv`) and local fallback files.

---

## 8. External API Dependencies

1. **OpenRouter API (`https://openrouter.ai/api/v1`):** For real-time LLM chat inference.
2. **Google Cloud Firestore / Firebase Auth:** For cloud synchronization of student tests and authentication.
3. **Public CDNs:**
   * Google Fonts (`fonts.googleapis.com`)
   * FontAwesome (`cdnjs.cloudflare.com`)
   * MathJax 3 (`cdn.jsdelivr.net`)
   * Lucide Icons (`unpkg.com`)
   * Chart.js (`cdn.jsdelivr.net`)
   * Canvas-Confetti (`cdn.jsdelivr.net`)

---

## 9. Potential Deployment Blockers

1. **Incomplete Dockerfile:**
   * `Dockerfile` line 15 currently reads: `COPY app.py app.py`.
   * **Blocker:** It fails to copy supporting modules (`adaptive_tutor.py`, `retrieval_engine.py`, `syllabus.py`, etc.) and the `data/` directory. A container built with this Dockerfile will crash on startup with `ModuleNotFoundError: No module named 'adaptive_tutor'`.
   * *Resolution:* Update Dockerfile to `COPY . /app` or explicitly copy all `.py` files and `data/`.
2. **CORS Restrictions in Production:**
   * `ALLOWED_ORIGINS` defaults to localhost ports (`5000, 5173, 5500, 8000`).
   * **Blocker:** If the frontend is deployed to a production domain (e.g. `https://bioneetpro.com`), the browser will reject API calls due to CORS unless `ALLOWED_ORIGINS` is configured with the production domain.
3. **Hardcoded Localhost in Frontend:**
   * `BioNeet-Pro.html` lines 1500 and 3455 fall back to `http://127.0.0.1:5000`.
   * **Blocker:** In production, students visiting the site remotely will fail to reach the backend unless `window.BIONEET_AI_BACKEND_URL` is set to the public backend endpoint.
4. **Stateless Multi-Instance In-Memory Limitations:**
   * In-memory rate limiting (`_rate_buckets` in `app.py`) is stored in Python memory.
   * **Blocker:** If multiple container instances or Gunicorn workers are spawned, rate limits and chat session buffers will not be shared across processes without an external Redis store.

---

## 10. Whether Vercel Appears Suitable

### Frontend: YES (Fully Suitable)
* `BioNeet-Pro.html` is a static HTML page with client-side JavaScript. It can be deployed directly to Vercel Static Hosting without any modifications.

### Backend: NO (Not Recommended for Vercel Serverless)
Deploying the Flask backend to Vercel Serverless Functions presents critical blockers:
1. **Bundle Size Limit:** Vercel serverless functions have a 250 MB uncompressed limit. The Python runtime dependencies (`pandas`, `scikit-learn`, `numpy`, `scipy`, `firebase-admin`) total ~355 MB, exceeding the limit.
2. **Read-Only Ephemeral Filesystem:** Vercel functions execute in an ephemeral environment with a read-only filesystem (except `/tmp`). The application's local file fallback mechanism (`data/student_profiles/`, `data/chat_threads/`) will fail when writes are attempted.
3. **Timeout Limits:** Free/Hobby Vercel plans have a strict 10-second function timeout. Multi-step RAG retrieval plus external OpenRouter LLM generation often takes 6-12 seconds, resulting in HTTP 504 Gateway Timeouts.
4. **SSE Streaming Support:** Server-Sent Events (`/api/tutor/answer/stream`) require long-lived connections that are poorly suited to serverless function lifecycles.

**Recommendation:** Deploy the frontend to Vercel / Cloudflare Pages / Firebase Hosting, and deploy the backend as a containerized web service to **Google Cloud Run**, **Render**, **Railway**, or **AWS App Runner**.

---

## 11. Whether a Separate Backend Appears Necessary

**YES.**  
A dedicated Python backend is necessary because:
1. The AI RAG engine uses Python scientific libraries (`scikit-learn` and `pandas`) for TF-IDF vector retrieval across 774 NCERT chunks.
2. The server protects secret credentials (`OPENROUTER_API_KEY`, Firebase service account private key) from client-side exposure.
3. The content safety guardrail, syllabus validator, and Bayesian Knowledge Tracing algorithms are fully implemented in Python.
