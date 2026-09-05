# AUDIT_README.md — BioNEET Pro Technical Architecture & Audit Map

> **Notice to Technical Reviewer:**  
> This repository contains the complete, unrefactored codebase for **BioNEET Pro**. No business logic, APIs, frontend UI, database schemas, or algorithms have been modified. This document provides the technical architectural map, system dependencies, data flows, and security profiles to facilitate a thorough and reliable audit.

---

## 1. Project Overview

* **Project Name:** BioNEET Pro
* **Purpose:** A comprehensive, context-sensitive NEET (National Eligibility cum Entrance Test) Biology exam preparation platform. It combines an authoritative NCERT-grounded AI tutoring engine, adaptive diagnostic testing, spaced-repetition flashcards (SM-2 / Leitner), biological concept graph modeling, automated score prediction, and an administrative curriculum portal.
* **Current Status:** Fully operational production prototype. The system features a single-file modular client (`BioNeet-Pro.html`) communicating with a Python Flask REST/SSE backend (`app.py`), backed by Google Cloud Firestore with a zero-credential local file fallback under `data/`.

---

## 2. Technology Stack

### Frontend
* **Core Runtime:** Vanilla HTML5, CSS3 (CSS Custom Properties), ECMAScript 2022 (`<script type="module">`).
* **Design & Typography:** Instrument Serif, Syne, JetBrains Mono via Google Fonts; custom responsive CSS.
* **UI Components & Icons:** FontAwesome 6.4.0, Lucide Icons.
* **Math & Scientific Notation:** MathJax 3 (for LaTeX biological and chemical formulas).
* **Analytics & Visualizations:** Chart.js (for student accuracy radar, score history, and unit mastery charts).
* **Gamification:** Canvas-Confetti (for test completion and streak milestones).
* **Cloud Client SDK:** Firebase Modular SDK v11.0.0 (`firebase-app.js`, `firebase-auth.js`, `firebase-firestore.js`).
* **Serving Model:** Static Single Page Application (SPA), typically hosted via VS Code Live Server (port 5500) during development, or any static hosting service.

### Backend
* **Runtime:** Python 3.10+ (tested and verified on Python 3.13.7).
* **Web Framework:** Flask 3.1.2.
* **Cross-Origin Resource Sharing:** `flask-cors` 6.0.1.
* **Data Processing & Machine Learning:**
  * `pandas` >= 2.2.0 (Knowledge base dataframes, student tracking matrices).
  * `scikit-learn` >= 1.4.0 (TF-IDF vectorizer, cosine similarity metrics for RAG retrieval).
  * `numpy` >= 1.26.0 (Vector arithmetic and score prediction heuristics).
* **Cloud Database Client:** `firebase-admin` >= 6.0.0 (Google Cloud Firestore client with service account authentication).
* **HTTP & Environment:** `requests` 2.32.5, `python-dotenv` 1.2.1.
* **PDF Ingestion & Parsing:** PyMuPDF (`fitz`, used in `ncert_ingestion.py` and `figure_extractor.py`).

### AI & External Integrations
* **LLM Gateway:** OpenRouter API (`https://openrouter.ai/api/v1` or custom endpoint e.g., `https://router.bynara.id/v1`).
* **Default LLM Model:** `openai/gpt-4o-mini` (configurable to any OpenRouter-supported model).
* **Fallback Engine:** Fully offline deterministic fallback controller (`fallback_controller.py`) that serves exact NCERT extracts when LLM APIs are unreachable, unconfigured, or rate-limited.

---

## 3. Architecture

The application follows a dual-tier decoupled architecture:
1. A **Client SPA** that directly accesses Firebase Auth and Firestore for client-side state and administrative writes.
2. A **Python Flask AI Engine** that hosts the Retrieval-Augmented Generation (RAG) pipeline, content classification, policy safety gates, MCQ generation, score prediction, and Bayesian Knowledge Tracing.

```
+-----------------------------------------------------------------------------------+
|                                 BROWSER CLIENT                                    |
|                               (BioNeet-Pro.html)                                  |
|                                                                                   |
|  [SPA Navigation]    [Live Server Reload Guard]    [Exam Integrity Watchdog]      |
|  [MathJax Rendering] [Chart.js Performance UI]     [Flashcard SM-2 Interface]     |
+-------------------------+-----------------------------------+---------------------+
                          |                                   |
                          | Direct Client SDK                 | HTTP REST / SSE Stream
                          | (Auth, Results, Videos)           | (Doubt Resolution, MCQs)
                          v                                   v
+------------------------------------+  +-------------------------------------------+
|          FIREBASE CLOUD            |  |             FLASK AI BACKEND              |
|                                    |  |                 (app.py)                  |
|  - Firebase Auth (Email/Password)  |  |                                           |
|  - Cloud Firestore (Nam5)          |  |  [CORS Middleware & Rate Limiting (IP)]   |
|    * users/{uid}                   |  |  [Content Classifier (content_classifier)]|
|    * results/{resultId}            |  |  [Policy Engine Gate (policy_engine.py)]  |
|    * mcqs/{mcqId}                  |  |  [Syllabus Validator (syllabus.py)]       |
|    * videos/{videoId}              |  |  [Concept Normalizer & Graph]             |
|    * updates/{updateId}            |  |  [NLP Anaphora Pipeline (nlp_pipeline)]   |
+-----------------+------------------+  +---------------------+---------------------+
                  ^                                           |
                  | Admin SDK                                 v
                  | Reads/Writes            +---------------------------------------+
                  |                         |        HYBRID RETRIEVAL ENGINE        |
                  |                         |         (retrieval_engine.py)         |
                  |                         |                                       |
                  |                         |  - NCERT Chunks TF-IDF (774 chunks)   |
                  |                         |  - NEET Knowledge Base CSV (335 rows) |
                  |                         +-------------------+-------------------+
                  |                                             |
                  |                                             v
+-----------------+------------------+      +---------------------------------------+
|        PERSISTENCE LAYER           |      |        ADAPTIVE TUTOR ENGINE          |
|       (firestore_store.py)         |      |          (adaptive_tutor.py)          |
|                                    |      |                                       |
| - Firestore-First Strategy         |      |  - Prompt Assembly & NCERT Grounding  |
| - Automatic Graceful Local File    |<-----+  - OpenRouter API (Primary LLM)       |
|   Fallback under data/ directory   |      |  - Offline Fallback (fallback_ctrl)   |
|   (profiles, dialogue, states)     |      |  - Response Validator (faithfulness)  |
+------------------------------------+      +---------------------------------------+
```

---

## 4. Important Directories and Files

| Directory / File | Description |
|---|---|
| `BioNeet-Pro.html` | The primary frontend application (4,922 lines). Self-contained SPA featuring all 20 student and admin views, live test proctoring, doubt solver, and flashcards. |
| `app.py` | Main Flask server (1,189 lines). Defines REST endpoints, Server-Sent Events (SSE), IP rate limiting, CORS configuration, and links all core tutoring modules. |
| `adaptive_tutor.py` | Single-brain AI tutoring orchestrator. Handles prompt engineering, external LLM calls, deterministic fallback switching, response validation, and BKT mastery progression. |
| `content_classifier.py` | Two-tier query classification system. Evaluates if student queries are in-syllabus NEET Biology, out-of-syllabus (Physics/Chem/General), or adversarial attacks. |
| `policy_engine.py` | Guardrail gatekeeper. Enforces boundaries, refuses non-biology prompts, and blocks prompt injection or jailbreak attempts. |
| `syllabus.py` | Canonical syllabus validator. Manages the official 32 NCERT Biology chapters (Class 11: 19 chapters, Class 12: 13 chapters) and validates concepts. |
| `concept_graph.py` | Concept dependency graph module. Loads `data/concept_dependency_graph.csv` to trace prerequisites and learning pathways. |
| `concept_normalizer.py` | Synonym and biological terminology normalizer. Maps colloquial student inputs to NCERT textbook terminology. |
| `nlp_pipeline.py` | Multi-turn NLP processing pipeline. Performs pronoun and anaphora resolution, entity extraction, and query expansion across chat history. |
| `retrieval_engine.py` | Dual-corpus hybrid retriever. Combines TF-IDF indexing over 774 NCERT textbook chunks and curated NEET knowledge base records. |
| `response_validator.py` | Post-generation safety filter. Verifies factual faithfulness, checks NCERT citation alignment, and detects potential hallucinations. |
| `fallback_controller.py` | Deterministic offline doubt solver. Generates structured biological answers with NCERT citations when external AI APIs are disabled or fail. |
| `learner_model.py` | Student profiling and Bayesian Knowledge Tracing (BKT) engine. Tracks concept mastery per student and updates probability matrices. |
| `mcq_engine.py` | Question generation and evaluation engine. Validates answers, records chapter accuracy, and provides diagnostic explanations. |
| `score_predictor.py` | Machine learning / heuristic NEET Biology score predictor (0–360 score scale) based on test performance, syllabus coverage, and accuracy. |
| `flashcard_backend.py` | Spaced-repetition Leitner/SM-2 flashcard review scheduling system. |
| `firestore_store.py` | Authoritative persistence abstraction layer. Manages Firestore operations via Firebase Admin SDK with automatic local JSON fallback in `data/`. |
| `ncert_ingestion.py` | Text parsing and chunking pipeline. Ingests NCERT PDFs to produce `data/ncert_textbook_index.json`. |
| `figure_extractor.py` | Diagram and table extractor. Extracts figure references, captions, and tables from textbooks. |
| `data/` | Core runtime data store: 774 textbook chunks (`ncert_textbook_index.json`), concept graphs, MCQ seeds, and local student profile fallbacks. |
| `datasets/` | Auxiliary question datasets (`test1.csv`). |
| `scripts/` | Diagnostic, validation, and Kaggle ingestion utility scripts. |
| `tests/` | Unit, regression, and syllabus boundary test suites. |
| `benchmark/` | Adversarial and classification benchmark datasets and evaluation runners. |
| `firestore.rules` | Production Cloud Firestore security rules with role-based access control. |
| `firebase.json` | Firebase configuration for Firestore database, indexes, and rules. |
| `requirements.txt` | Python dependency specifications. |
| `Dockerfile` | Container configuration for backend deployment. |

---

## 5. Application Flow

### 1. User Registration & Authentication
```
User -> Enters Email/Password on #page-register
     -> Firebase Auth createUserWithEmailAndPassword()
     -> Creates users/{uid} document with {role: "student"}
     -> Redirects to #page-dashboard
```

### 2. Student Dashboard & Diagnostics
```
User -> Visits #page-dashboard
     -> Loads cached results and mastery from Firestore (or LocalStorage fallback)
     -> Fetches score prediction from GET /api/predict/score?student_id={uid}
     -> Renders Chart.js radar charts and chapter mastery heatmaps
```

### 3. AI Tutor Doubt Solving (Chat & Step Mode)
```
User -> Submits question on #page-ai-tutor (with optional chapter/topic context)
     -> Frontend POSTs to /api/tutor/answer or /api/tutor/answer/stream (SSE)
     -> app.py enforces token-bucket rate limit (20 req / 60s per IP)
     -> content_classifier.py checks query safety & subject boundary
     -> If Out-of-Syllabus: policy_engine.py immediately returns polite refusal
     -> If In-Syllabus:
        - nlp_pipeline.py resolves anaphora ("What does it do?" -> "What does SA node do?")
        - retrieval_engine.py finds top-k NCERT chunks and KB rows
        - adaptive_tutor.py builds prompt with NCERT grounding
        - OpenRouter API invoked (or fallback_controller if offline/error)
        - response_validator.py checks faithfulness against NCERT chunks
        - learner_model.py updates student mastery for detected concept
     -> Response streamed/returned to frontend with confidence score & citations
```

### 4. Mock Test & Anti-Cheat Examination
```
User -> Selects chapter on #page-mcq and clicks "Start Test"
     -> Backend generates or loads verified NCERT MCQs
     -> Timer arms; Exam Watchdog enters fullscreen mode
     -> If student tabs away / blurs window: anti-cheat records violation
     -> On submit: score computed, answers explained, result stored in Firestore results/{resultId}
```

### 5. Flashcard Spaced Repetition (SM-2)
```
User -> Opens #page-flashcards
     -> GET /api/flashcards/due?student_id={uid}
     -> Student rates recall quality (0–5)
     -> POST /api/flashcards/review updates SM-2 interval, repetitions, and ease-factor
     -> State persisted in Firestore flashcards/{studentId} (or local JSON fallback)
```

---

## 6. Authentication & Authorization

* **Provider:** Firebase Authentication (Email/Password).
* **Roles:**
  1. `student`: Default role assigned at registration. Restricted to reading/writing their own profile, test results, flashcards, and tutor chats.
  2. `admin`: Elevated management role. Authorized in `firestore.rules` via custom claims (`request.auth.token.admin == true`) OR via `users/{uid}.data.role == "admin"`.
* **Authorization Implementation:**
  * Client-side route guards in `BioNeet-Pro.html` prevent unauthorized access to `#page-admin-*`.
  * Backend verifies Firebase ID tokens via `firebase_admin.auth.verify_id_token()`
    (2026-09-05 hardening). With `REQUIRE_FIREBASE_AUTH=true`, caller-supplied
    IDs are never trusted (401 without a valid token); admin endpoints
    (`/api/tutor/tracker`, `/api/tutor/import-kaggle`, `/api/mcqs/generate`)
    require a verified admin (custom claim or server-side `users/{uid}` role);
    `/api/learner/profile` is self-or-admin. See `API_ACCESS_CONTROL.md`.
  * Cloud Firestore rules (`firestore.rules`) enforce strict document-level security:
    * `users/{userId}`: Only owner can read/update; role creation restricted to "student".
    * `results/{resultId}`: Only authenticated owner can write results.
    * `mcqs/{mcqId}`, `videos/{videoId}`, `updates/{updateId}`: Public read, admin-only write.
    * `flashcards/{studentId}`, `learner_profiles/{studentId}`, `dialogue_states/{studentId}`: Owner or admin access only.

---

## 7. Database Architecture

* **Database Provider:** Google Cloud Firestore (Nam5 / default).
* **Dual Persistence Model:**  
  The application implements a **Firestore-first, local-file-fallback** design via `firestore_store.py`. If Firebase Admin credentials (`serviceAccount.json` or `FIREBASE_SERVICE_ACCOUNT` env) are present, data persists to Cloud Firestore. If credentials are not supplied, all operations fall back to local JSON files in `data/` without raising exceptions or breaking runtime execution.

### Collections & Local Directory Mapping

| Firestore Collection | Local File Fallback Path | Access Level | Description |
|---|---|---|---|
| `users` | N/A (Firebase Auth) | Owner / Admin | User profile and role document |
| `results` | `data/results/` | Authenticated | Test submissions and scores |
| `mcqs` | `data/indexed_mcqs_cache.json` | Public Read / Admin Write | Curated NEET Biology MCQ bank |
| `videos` | In-memory / seed | Public Read / Admin Write | Educational lecture video links |
| `updates` | In-memory / seed | Public Read / Admin Write | NEET examination news & announcements |
| `flashcards` | `data/flashcard_state/{student_id}.json` | Owner / Admin | Leitner / SM-2 spaced repetition decks |
| `learner_profiles` | `data/student_profiles/{student_id}.json` | Owner / Admin | Concept-level mastery vectors & BKT states |
| `dialogue_states` | `data/dialogue_states/{student_id}.json` | Owner / Admin | Multi-turn conversational memory |
| `score_predictions` | `data/score_predictions/{student_id}.json` | Owner / Admin | Historical NEET score predictions |
| `tutor_states` | `data/tutor_states/{student_id}.json` | Owner / Admin | Active tutoring sessions & steppers |
| `chat_threads` | `data/chat_threads/{student_id}.json` | Owner / Admin | Chat turn history (capped at 30 turns) |

---

## 8. AI & LLM Integration

* **Gateway Provider:** OpenRouter API (`https://openrouter.ai/api/v1` or custom base URL).
* **Model Configuration:** Configured via `OPENROUTER_MODEL` (default: `openai/gpt-4o-mini`).
* **Origin of AI Requests:** Server-side only (`adaptive_tutor.py` via `requests.post`). The client never directly calls OpenRouter.
* **System Prompt:**
  ```text
  You are BioNEET Pro AI Tutor - an expert NEET Biology teacher.
  Your answers must be clear, concise, student-friendly, and aligned with NCERT.
  Use bullets where useful, include NEET tips, and keep answers under 300 words unless more detail is needed.
  You are context-sensitive: adapt your answer using the student's selected chapter, topic, exam goal, and recent chat history when provided.
  ```
* **Grounding & RAG Context:** Top-k retrieved chunks from `data/ncert_textbook_index.json` (774 textbook chunks) and `data/neet_knowledge_base.csv` (335 curated concept rows) are injected into the prompt.
* **Response Validation:** `response_validator.py` computes lexical and semantic overlap between the LLM output and the NCERT context chunks. If faithfulness falls below threshold or hallucinations are detected, the response is flagged or replaced with verified text.
* **Rate Limiting:** In-memory token bucket rate limiter in `app.py` enforces a maximum of 20 requests per 60-second window per client IP address.
* **Fault Tolerance & Fallback:** If OpenRouter returns HTTP 4xx/5xx, times out, or fails to authenticate, `fallback_controller.py` intercepts the request and generates a complete, structured NCERT-grounded response with chapter citations.

---

## 9. Environment Variables Specification

The system recognizes the following environment variables (defined in `.env.example`):

### Server-Side Variables (Flask Backend)
```text
OPENROUTER_API_KEY=          # Secret API key for OpenRouter LLM gateway
OPENROUTER_MODEL=            # Model ID (default: openai/gpt-4o-mini)
OPENROUTER_BASE_URL=         # Optional custom base URL for OpenRouter/proxy
AI_API_BASE_URL=             # Alias for OPENROUTER_BASE_URL
AI_MAX_TOKENS=               # Maximum response token length (default: 550)
ALLOWED_ORIGINS=             # Comma-separated CORS allowed origins
RATE_LIMIT_WINDOW_SECONDS=   # Rate limit duration window (default: 60)
RATE_LIMIT_MAX_REQUESTS=     # Maximum requests allowed per window (default: 20)
FLASK_DEBUG=                 # Flask debug mode flag (true/false)
PORT=                        # Backend HTTP port (default: 5000)
FIREBASE_SERVICE_ACCOUNT=    # Path to serviceAccount.json file
FIREBASE_SERVICE_ACCOUNT_JSON=# Optional inline JSON string of service account credentials
```

### Client-Side Variables (Frontend Build / Runtime)
```text
VITE_FIREBASE_API_KEY=       # Public Firebase Web Client API Key
VITE_FIREBASE_AUTH_DOMAIN=   # Firebase Auth domain
VITE_FIREBASE_PROJECT_ID=    # Firebase Project ID
VITE_FIREBASE_STORAGE_BUCKET=# Firebase Cloud Storage bucket
VITE_FIREBASE_MESSAGING_SENDER_ID= # Firebase messaging sender ID
VITE_FIREBASE_APP_ID=        # Firebase Web App ID
VITE_AI_BACKEND_URL=         # URL of the Python Flask backend (default: http://127.0.0.1:5000)
VITE_ENABLE_DEMO_MODE=       # Client demo mode toggle (true/false)
```

---

## 10. Deployment Overview

* **Frontend:** Static HTML/JS. Can be deployed to any static host (Cloudflare Pages, Firebase Hosting, Vercel, Netlify, AWS S3).
* **Backend:** Python WSGI web service. Requires a persistent Linux/Docker container with Python 3.10+ and C-extensions for `scikit-learn`, `numpy`, and `pandas`.
* **Recommended Backend Platforms:** Google Cloud Run, AWS App Runner, Render, Railway, or VPS (Ubuntu + Gunicorn).
* **Suitability for Vercel:**
  * Frontend: **Fully Compatible**.
  * Backend: **Not Recommended on Vercel Serverless** due to Python package bundle size limits (~350MB uncompressed dependencies), 10s execution timeouts, ephemeral read-only filesystem (incompatible with local JSON fallback in `data/`), and stateless lambda execution breaking in-memory rate limiting and SSE streaming.
* **Containerization:** A `Dockerfile` is provided for containerized deployments (see `DEPLOYMENT_NOTES.md` regarding build considerations).
