# BioNEET Pro — Comprehensive Technical Project Map & System Handover

> **Version**: 2.4.0-production (NEET UG Target Cohorts: 2027 / 2028)  
> **Prepared For**: Technical Review, Codebase Handover & External Architecture Audit  
> **Repository Root**: `BioNEETPro/`

---

## 1. What BioNEET Pro Does

**BioNEET Pro** is an authoritative, NCERT-aligned AI learning and exam preparation platform designed specifically for students taking the National Eligibility cum Entrance Test (NEET UG Biology) in India.

The platform bridges self-paced learning with intelligent pedagogical guardrails:
1. **Interactive Single-Page Application (SPA)**: Provides an ultra-fast, responsive dashboard for students with 0ms client-side route transitions, 3D animated DNA canvas visualizer, chapter-by-chapter mastery trackers, and real-time updates.
2. **Pedagogical AI Tutor ("Dr. Arya")**: An NCERT-bounded conversational biology mentor equipped with dual-corpus RAG retrieval, strict out-of-syllabus refusal filters, prompt-injection defense, multi-turn dialogue memory, in-chat MCQ batch generation, and Web Speech API text-to-speech voice narration.
3. **Smart Mock Tests & Adaptive Assessment**: Full-length 720/360-score mock exams and chapter-specific drills. Features live countdown timers, tab-switch anti-cheat / exam integrity auto-submission, interactive OMR review sheet, and detailed AI explanations for every single option.
4. **Gamified "Bio Arcade & Memory Arena"**: A dedicated interactive game suite that turns passive textbook reading into active recall:
   - **🧬 BioMatch**: 12-card associative pair matching (Concepts, Organelles, Mechanisms, and Scientists).
   - **⚡ Speed Sorter**: 30-second rapid classification rush with keyboard shortcuts (`← Left` / `Right →`) and streak bonus multipliers.
   - **💣 Trap Breaker**: NTA trap detection where students spot deceptive wording (e.g., millimeter vs micrometer, radioactive vs heavy isotope).
   - **🗂️ Active Flashcards**: Spaced repetition engine implementing the 5-box Leitner system.
5. **AI Coach & Score Predictor**: Continuous evaluation of past test performances to diagnose the student's weakest chapter, calculate expected NEET percentile/rank, and generate daily personalized coaching advice.
6. **Curated Video & Textbook Library**: Direct streaming access to top NEET educator YouTube lectures mapped chapter-by-chapter and authoritative NCERT chapter downloads.
7. **Comprehensive Admin Portal**: Real-time multi-device student synchronization, live registration metrics, chapter performance analytics, and full CRUD management for MCQs, videos, and platform announcements.

---

## 2. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI / Client** | HTML5, Modern CSS3 (CSS Variables, Flexbox/Grid, Glassmorphism), Vanilla JavaScript (ES Modules), HTML5 Canvas 2D/3D Context API, Web Speech API (`SpeechSynthesis`) |
| **Client Cloud SDK** | Firebase Web SDK v11 (Authentication, Cloud Firestore with real-time `onSnapshot` subscriptions) |
| **Backend Web Framework** | Python 3.10+ / Flask 3.1, Flask-CORS 6.0, Gunicorn 21.0 WSGI server |
| **AI / LLM Gateway** | OpenRouter REST API (`https://openrouter.ai/api/v1`) with fallback model routing (`openai/gpt-4o-mini`, `agnes-2.5-flash`) |
| **RAG & NLP Retrieval** | `scikit-learn` (`TfidfVectorizer`, Cosine Similarity), `pandas`, `numpy`, custom N-gram tokenizer and character-level sliding window fallback |
| **Document Ingestion** | Custom PDF extraction engine (`ncert_ingestion.py`, `PyPDF2`, `pdfplumber`) parsing 38 NCERT textbooks into structured JSON chunks |
| **Data Persistence** | Dual-tier hybrid: Google Cloud Firestore (production) + Local atomic JSON/CSV stores in `data/` (offline/development fallback) |
| **Containerization & Hosting** | Docker (`Dockerfile`), Vercel (Frontend SPA), Render (Backend Flask API) |

---

## 3. Application Architecture

```
                                  ┌────────────────────────┐
                                  │   Student / Browser    │
                                  │ (Vercel: index.html)   │
                                  └───────────┬────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
        [Firebase Auth & Firestore]                             [Flask REST API]
     (Direct client SDK: Auth, sync)                     (Render: app.py / Gunicorn)
                    │                                                   │
                    ▼                                                   ▼
       ┌────────────────────────┐                          ┌────────────────────────┐
       │ Google Cloud Firestore │                          │ API Rate Limiting &    │
       │ - Users / Profiles     │                          │ Security Gateways      │
       │ - Test Results         │                          └───────────┬────────────┘
       │ - Admin MCQs & Videos  │                                      │
       └────────────────────────┘                                      ▼
                                                           ┌────────────────────────┐
                                                           │  Syllabus Purity Gate  │
                                                           │  (38 NCERT Chapters)   │
                                                           └───────────┬────────────┘
                                                                       │
                                              ┌────────────────────────┴────────────────────────┐
                                              │                                                 │
                                              ▼                                                 ▼
                                  ┌───────────────────────┐                         ┌───────────────────────┐
                                  │  Dual-Corpus TF-IDF   │                         │ Concept Dependency    │
                                  │  Retrieval Engine     │                         │ Graph Resolution      │
                                  │  - KB CSV             │                         │ - Prerequisites       │
                                  │  - NCERT Textbook JSON│                         │ - NEET Traps          │
                                  └───────────┬───────────┘                         └───────────┬───────────┘
                                              │                                                 │
                                              └────────────────────────┬────────────────────────┘
                                                                       │
                                                                       ▼
                                                           ┌────────────────────────┐
                                                           │  OpenRouter LLM Proxy  │
                                                           │  (Dr. Arya Persona)    │
                                                           │  [Fallback: Local RAG] │
                                                           └───────────┬────────────┘
                                                                       │
                                                                       ▼
                                                           ┌────────────────────────┐
                                                           │ Output Fact Validator  │
                                                           │ & NCERT Citations      │
                                                           └────────────────────────┘
```

The system employs a **decoupled, dual-tier architecture**:
1. **Edge Client Tier**: The frontend runs entirely client-side without a Node.js SSR runtime. It handles state transitions, instant page routing via hash/DOM management, and connects directly to Firebase for low-latency CRUD operations and real-time student updates.
2. **Intelligence API Tier**: The Flask backend serves as the authoritative biology domain gatekeeper. It does not blindly forward student queries to an LLM; instead, every interaction passes through an automated pipeline: input rate limiting -> syllabus verification -> dual-corpus semantic retrieval -> prompt construction -> LLM generation -> factual validation.

---

## 4. Important Folders and Files

```
BioNEETPro/
├── index.html                   # Primary Single-Page Application (HTML, CSS, JS modules)
├── BioNeet-Pro.html             # Synced distribution mirror of index.html
├── app.py                       # Main Flask web application, route handlers, and middleware
├── adaptive_tutor.py            # Core Dr. Arya tutoring state machine, context, and prompts
├── retrieval_engine.py          # Dual-corpus TF-IDF semantic vector space retrieval
├── syllabus.py                  # Authoritative 38 NCERT chapters registry & out-of-syllabus filter
├── concept_graph.py             # Knowledge graph mapping concept prerequisites & associations
├── mcq_engine.py                # Adaptive test generator, grading engine, and distractor validator
├── score_predictor.py           # NEET rank & percentile predictor based on student performance
├── learner_model.py             # Bayesian student mastery tracker & spaced-repetition profile
├── ncert_ingestion.py           # Pipeline for converting NCERT PDFs into chunked JSON indexes
├── firestore_store.py           # Server-side Firebase Firestore connector with local file fallbacks
├── response_validator.py        # Post-generation factual verifier against NCERT statements
├── content_classifier.py        # Adversarial prompt & off-topic injection detection
├── dialogue_state.py            # Multi-turn conversation state representation
├── fallback_controller.py       # Deterministic rule-based local fallback when LLM is offline
│
├── data/                        # Processed authoritative knowledge bases & local caches
│   ├── ncert_textbook_index.json # 38 parsed NCERT chapters (paragraphs, chunks, metadata)
│   ├── neet_knowledge_base.csv   # Curated high-yield biological facts and relationships
│   ├── syllabus_registry.json    # Canonical NCERT syllabus registry (weightages, chapters)
│   ├── concept_dependency_graph.csv # Directed edges between biological concepts
│   ├── indexed_mcqs_cache.json   # Deduplicated master MCQ cache across all chapters
│   ├── chat_threads/             # Local student chat history JSONs
│   ├── dialogue_states/          # Local dialogue state caches
│   ├── flashcard_state/          # Local Leitner flashcard progress
│   ├── score_predictions/        # Historical score prediction snapshots
│   └── student_profiles/         # Student mastery profiles
│
├── Textbook/                    # Authoritative NCERT Biology Class 11 & 12 PDF textbooks
├── tests/                       # Complete automated unit and integration test suite
│   ├── test_security_regression.py # Security, path traversal, and auth tests
│   ├── test_guardrails.py          # Input injection, safety, and adversarial prompt tests
│   ├── test_mcq_chapter_purity.py  # Chapter categorization and purity verification
│   └── test_master_suite.py        # End-to-end master test suite
│
├── datasets/                    # Benchmark and validation datasets (test1.csv)
├── scripts/                     # Operational maintenance and sync scripts
├── docs/                        # Architecture documentation, audit reports, and deployment notes
├── Dockerfile                   # Production container definition for Flask backend
├── requirements.txt             # Python runtime dependencies
├── firebase.json                # Firebase hosting and rule configuration
├── firestore.rules              # Cloud Firestore security and access-control rules
├── .env.example                 # Safe environment variable template
└── PROJECT_MAP.md               # This system architecture and handover document
```

---

## 5. Main Entry Points

1. **Frontend Client**:
   - File: `index.html` (and `BioNeet-Pro.html`)
   - Initialization:
     - Bootstraps Firebase Web SDK (Auth + Firestore).
     - Resolves backend URL (`window.BIONEET_AI_BACKEND_URL` -> default `https://bioneetpro.onrender.com` or `localhost:5000` in dev).
     - Initializes `initHero3D()` for the 3D double helix Canvas animation.
     - Sets up hash-based SPA routing via `go(page)`.
     - Establishes Firestore `onSnapshot` real-time listeners for live updates.
2. **Backend Server**:
   - File: `app.py`
   - Entry Command: `python app.py` (Development) or `gunicorn app:app --bind 0.0.0.0:$PORT` (Production).
   - Initializes RAG indexes (`retrieval_engine.init_engine()`), syllabus validator, learner manager, and rate limiting stores.
3. **Data Ingestion CLI**:
   - File: `ncert_ingestion.py`
   - Command: `python ncert_ingestion.py`
   - Scans `Textbook/*.pdf`, computes SHA-256 checksums, extracts section headings, paragraphs, and tables, and writes `data/ncert_textbook_index.json`.

---

## 6. Authentication Flow

BioNEET Pro uses a **multi-tier authentication model**:

```
[User Registration / Login]
         │
         ▼
[Firebase Web SDK v11] ─── Authenticates with Google Identity
         │
         ├── Issues Firebase JWT ID Token
         │
         ▼
[Client State (DB.currentUser)] ─── Populates local profile & role
         │
         ├── Attaches "Authorization: Bearer <ID_TOKEN>" to all API requests
         │
         ▼
[Flask Backend Middleware (app.py: auth_student_id)]
         │
         ├── Mode A: Strict Production (Default)
         │     └── Calls `firebase_admin.auth.verify_id_token(token)`
         │     └── Rejects invalid/expired tokens with HTTP 401/403
         │     └── Enforces student_id matches token UID
         │
         └── Mode B: Dev Mode (`DEV_AUTH_MODE=true` in .env.local)
               └── Permits caller-supplied `student_id` for local tests and sweeps
```

- **Client Role Guard**: Non-admin users attempting to navigate to `admin*` routes via `go(page)` are blocked immediately on the client and redirected with a warning toast.
- **Database Rules**: `firestore.rules` enforces that students can only read/write their own profiles, test results, and flashcard queues, while admin accounts (`role === 'admin'`) have global write access to MCQs, videos, and platform updates.

---

## 7. Database Architecture

The application implements a **hybrid dual-store**:

### Primary: Cloud Firestore (Production)
- **`users`**: `{ name, email, target: 'NEET 2027/2028', role: 'student'|'admin', joined, lastLoginAt, lastActive }`
- **`results`**: `{ student_id, chapter_id, mode, score, total, accuracy, answers, timestamp }`
- **`mcqs`**: `{ id, chapter, q, opts: [A, B, C, D], correct: 0..3, exp, diff: 'Easy'|'Medium'|'Hard' }`
- **`videos`**: `{ id, title, chapter, url, channel, thumb }`
- **`updates`**: `{ id, title, desc, date, priority: 'High'|'Medium'|'Low', type }`
- **`flashcards`**: `{ student_id, cards: [{ id, box: 1..5, nextReview, term, definition }] }`

### Secondary: Local JSON / CSV (Offline / Local Dev Fallback)
If Firebase credentials are not provided, `firestore_store.py` transparently redirects operations to atomic, locking JSON files inside `data/`:
- `data/chat_threads/{student_id}.json`
- `data/dialogue_states/{student_id}.json`
- `data/flashcard_state/{student_id}.json`
- `data/score_predictions/{student_id}.json`
- `data/student_profiles/{student_id}.json`

---

## 8. AI / LLM Architecture & RAG Pipeline

BioNEET Pro avoids generic LLM hallucination through a multi-stage **Retrieval-Augmented Generation (RAG)** pipeline:

```
User Query: "Why do C4 plants lack photorespiration?"
   │
   ▼
[Stage 1: Purity & Safety Gate (syllabus.py & content_classifier.py)]
   ├── Check against prompt injection & jailbreaks
   ├── Check against NEET UG Biology syllabus boundary
   └── If off-topic (e.g. "Write a poem", "Physics calculus"): REFUSED with friendly redirect
   │
   ▼
[Stage 2: Concept Extraction & Dependency Graph (concept_graph.py)]
   ├── Identifies core concepts: "C4 Pathway", "Photorespiration", "Kranz Anatomy", "RuBisCO"
   └── Traverses prerequisites & known NEET traps (e.g. bundle sheath cells lack grana)
   │
   ▼
[Stage 3: Dual-Corpus Hybrid Retrieval (retrieval_engine.py)]
   ├── Corpus A: neet_knowledge_base.csv (Curated high-yield facts)
   ├── Corpus B: ncert_textbook_index.json (Class 11 Chapter 13 chunk text)
   └── TF-IDF Cosine Scoring + Sliding character window fallback
   │
   ▼
[Stage 4: Prompt Assembly (adaptive_tutor.py)]
   ├── Injects Dr. Arya System Prompt (Pedagogical, NCERT-strict, encouraging)
   ├── Injects Top-K Retrieved NCERT Excerpts
   ├── Injects Recent Chat History & Student Dialogue State
   └── Sets constraints: Temperature 0.2, Max Tokens 550
   │
   ▼
[Stage 5: LLM Inference (OpenRouter API)]
   └── Models: openai/gpt-4o-mini, agnes-2.5-flash
   │
   ▼
[Stage 6: Output Fact Validation (response_validator.py)]
   ├── Cross-checks statements against NCERT terminology
   └── Ensures zero non-NCERT biological speculations
   │
   ▼
[Stage 7: Response Formatting]
   └── Delivered to UI with Markdown formatting, option to practice MCQs, and Text-to-Speech audio button
```

### Deterministic Local Fallback Engine
If the OpenRouter gateway experiences network timeouts or quota exhaustion, `fallback_controller.py` synthesizes a deterministic response directly from the top-scoring NCERT textbook chunks in `data/ncert_textbook_index.json`. The user never encounters an application crash or broken chat session.

---

## 9. How a User's Question Flows Through the System

1. **User Action**: The student types a question in the AI Tutor input box or taps a suggested high-yield concept pill (e.g. "🧬 Cell Cycle").
2. **Frontend Dispatch**:
   - Checks client network state and active chat thread.
   - Appends the user message bubble immediately (optimistic UI update).
   - Issues a `POST /api/chat` request to the backend with payload:
     `{ message, context, history, student_id }`.
3. **Backend Middleware**:
   - `client_ip()` checks request rate limit (max 20 requests / 60 seconds).
   - Validates payload length (max 256 KB).
4. **Syllabus & Guardrail Check**:
   - `syllabus_validator.is_in_syllabus(query)` checks if query belongs to the 38 NCERT chapters.
   - `content_classifier` evaluates if the query is an adversarial prompt.
5. **Retrieval**:
   - `retrieval_engine.retrieve(query)` returns the top 3-5 authoritative textbook chunks with chapter and page citations.
6. **LLM Generation / Fallback**:
   - Calls OpenRouter API. If successful, validates response.
   - If API fails, `fallback_controller.generate_fallback(query, retrieved_chunks)` generates a structured explanation.
7. **Client Rendering**:
   - Markdown headers, bold terms, bullet points, and high-yield traps are styled.
   - If the student requested practice questions, an interactive MCQ block is embedded directly into the chat thread with instant check buttons.
   - A `🔊 Listen` button is attached using browser speech synthesis with Dr. Arya's persona.

---

## 10. API Integrations

| Provider | Endpoint / Service | Purpose |
|---|---|---|
| **OpenRouter** | `https://openrouter.ai/api/v1/chat/completions` | Cloud LLM inference with automated fallbacks |
| **Google Firebase** | `https://identitytoolkit.googleapis.com` | User registration, password resets, and JWT verification |
| **Google Firestore** | `https://firestore.googleapis.com` | Real-time database sync for students, MCQs, and leaderboards |
| **YouTube** | `https://www.youtube-nocookie.com/embed/*` | Embedded curated biology lectures without intrusive tracking |
| **Web Speech API** | `window.speechSynthesis` | Client-side native Text-to-Speech narration for Dr. Arya |

---

## 11. Deployment Architecture

1. **Frontend (Vercel)**:
   - Git-integrated automated deployment on branch `main`.
   - Serves `index.html` as static content with edge CDN caching.
   - Dynamic client URL resolution points to the live backend on Render.
2. **Backend (Render)**:
   - Deployed as a web service running a Docker container (`Dockerfile`).
   - Base image: `python:3.11-slim`.
   - WSGI runner: `gunicorn --workers 2 --threads 4 --timeout 120 app:app`.
   - Automatic HTTPS termination.

---

## 12. Important Dependencies

### Python Backend (`requirements.txt`)
- `Flask==3.1.2`: Core HTTP routing and REST endpoints.
- `flask-cors==6.0.1`: Cross-Origin Resource Sharing handling.
- `requests==2.32.5`: Outbound HTTP requests to OpenRouter and external services.
- `python-dotenv==1.2.1`: Environment variable management.
- `pandas>=2.2.0`, `numpy>=1.26.0`: Tabular data processing for MCQ banks and trackers.
- `scikit-learn>=1.4.0`: TF-IDF vectorization and cosine similarity calculations.
- `firebase-admin>=6.0.0`: Server-side Firebase token verification and Firestore administration.
- `gunicorn>=21.0.0`: Production WSGI HTTP server.

### Frontend Client
- Google Firebase JavaScript SDK v11 (ESM modules loaded via `gstatic.com`).
- Google Fonts (`Instrument Serif`, `Plus Jakarta Sans`, `JetBrains Mono`).

---

## 13. Current Status & Experimental Features

1. **Production-Ready Features**:
   - 100% complete 38-chapter NCERT Biology curriculum coverage.
   - Full mock test suite with timed exam mode and OMR sheet.
   - 4-mode Bio Arcade & Gamification Arena (BioMatch, Speed Sorter, Trap Breaker, Leitner Flashcards).
   - Real-time Firestore synchronization between student laptops and admin portal.
   - Responsive design tested across desktop, tablet, and mobile displays.
2. **In-Progress / Experimental Modules**:
   - `figure_extractor.py`: Automated diagram and figure label extractor from NCERT PDFs for visual diagram-based MCQs.
   - `learner_model.py`: Multi-turn Bayesian Knowledge Tracing (BKT) to dynamically calibrate MCQ difficulty to each student's exact skill level.
   - `kaggle_imports/`: Bulk offline MCQ ingestion tool for importing and deduplicating external competitive exam datasets.

---
*End of BioNEET Pro Project Map & System Handover Document.*
