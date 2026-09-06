# BioNEETPro V3 — Baseline Inspection & Audit Report (`V3_BASELINE.md`)

*Established Date:* September 6, 2026  
*Status:* **ALL V2 CRITICAL VERIFICATIONS & TESTS PASSING (100%)**  
*Scope:* Pre-V3 Architectural Audit across Routes, Firebase, Auth, Roles, Assessments, and Frontend.

---

## 1. Test Suite & Quality Verification Baseline

| Verification Suite | Command | Total Tests / Points | Passed | Failed | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Master Discovery Test Suite** | `python -m unittest discover -s tests` | 108 | 108 | 0 | **100.0%** |
| **30-Point Mission-Critical Gate** | `python tests/verify_30_points.py` | 30 | 30 | 0 | **100.0%** |
| **Interactive MCQ Evaluation Suite** | `python -m unittest tests/test_interactive_mcq_evaluation.py` | 7 | 7 | 0 | **100.0%** |
| **V2 Ecosystem Suite** | `python -m unittest tests/test_v2_ecosystem.py` | 6 | 6 | 0 | **100.0%** |
| **Aggressive AI Tutor Suite** | `python -m unittest tests/test_ai_tutor_aggressive.py` | 17 | 17 | 0 | **100.0%** |
| **MCQ Pool Integrity & Validation** | `python -m unittest tests/test_mcq_validation.py` | 5 | 5 | 0 | **100.0%** |

### Verified Subsystem Health:
- **MCQ Question Pool:** 6,600 / 6,600 MCQs validated (100% compliant with 4 distinct options, verified answer keys, zero missing keys).
- **BKT Mathematics:** Verified correct updates ($0.50 \to 0.815$) and incorrect updates ($0.50 \to 0.25$).
- **HTML Invariant:** `index.html` and `BioNeet-Pro.html` match byte-for-byte (`SHA256: 269a2096b6f1f43e609f317bb7bf4aa9b00072deb435f736b8b43ecaf472674d`).

---

## 2. Current Route Inventory (`app.py`)

| Category | Endpoint | Methods | Auth / Role Gate | Current Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Public / Static** | `/` | GET | None | Serves root SPA (`index.html`) |
| **Public / Static** | `/<path:filename>` | GET | Path traversal guard | Serves static styles, scripts, images |
| **Public / Health** | `/health`, `/api/health`, `/api/ready` | GET | None | Health checks & readiness probes |
| **Curriculum** | `/api/curriculum` | GET | None | Canonical 33-chapter syllabus hierarchy |
| **Curriculum** | `/api/syllabus` | GET | None | Syllabus structure & NCERT mappings |
| **Textbook** | `/api/textbook/chapters` | GET | None | Chapter list |
| **Textbook** | `/api/textbook/pdf/<chapter_id>` | GET | None | Official NCERT PDF download |
| **Identity** | `/api/auth/me` | GET | Verified Bearer Token / Claims | Role resolution (`SUPER_ADMIN`, `TEACHER`, `STUDENT`) |
| **AI Assistant** | `/api/assistant/chat` | POST | Role-aware + Context | Global floating multi-role AI Assistant |
| **Tutor Engine** | `/chat`, `/ask`, `/api/tutor/answer` | POST | Student / Bearer | Single-brain Adaptive RAG Tutor |
| **Tutor Stepper** | `/api/tutor/step`, `/api/tutor/query` | POST | Student | Stepwise Socratic dialogue session |
| **Tutor Logs** | `/api/tutor/tracker` | GET | Student | BKT concept tracker |
| **Learner Profile** | `/api/learner/profile`, `/api/learner/review-due` | GET | Student | BKT mastery vector & Spaced Repetition items |
| **Flashcards** | `/api/flashcards`, `/api/flashcards/due`, `/review` | GET/POST/PATCH/DELETE | Student | SM-2 Spaced repetition flashcards |
| **Predictor** | `/api/score/predict`, `/api/score/history` | GET | Student | NEET rank & score projection |
| **MCQ Practice** | `/api/mcq/generate`, `/api/mcqs/generate` | POST | Student | On-demand adaptive practice test |
| **MCQ Submit** | `/api/mcq/submit`, `/api/mcq/submit-batch` | POST | Student | Practice answer grading |
| **Teacher Admin** | `/api/admin/teachers` | GET, POST | `SUPER_ADMIN` Only | Provision and list institutional teachers |
| **Teacher Admin** | `/api/admin/teachers/<id>`, `.../status` | PUT, PATCH | `SUPER_ADMIN` Only | Modify metadata & toggle status (`ACTIVE`/`INACTIVE`) |
| **Assessment Admin**| `/api/mcqs/ai-generate` | POST | `TEACHER` or `SUPER_ADMIN` | Authoring assistant generates questions with `PENDING_REVIEW` |
| **Assessment Admin**| `/api/mcqs/approve` | POST | `TEACHER` or `SUPER_ADMIN` | Review gate to approve questions into question bank |
| **Assessments** | `/api/assessments` | GET, POST | GET: Public/Student (scrubbed); POST: `TEACHER`/`ADMIN` | List and author assessments |
| **Assessments** | `/api/assessments/<id>`, `.../status` | GET, PUT, POST | GET: Role-filtered; PUT/POST: Owner/Admin | Lifecycle state transitions & updates |
| **Assessments** | `/api/assessments/upcoming` | GET | Student / All | Dedicated live & scheduled test window feed |
| **Assessments** | `/api/assessments/<id>/submit` | POST | Student | Live exam submission with duplicate lock |
| **Assessments** | `/api/assessments/<id>/my-result` | GET | Student | Student personal scorecard retrieval |
| **Assessments** | `/api/assessments/<id>/results` | GET | `TEACHER` (Owner) or `ADMIN` | Class roster results & question item analytics |

---

## 3. Firebase & Firestore Security Model Baseline (`firestore.rules`)

### Active Collections:
1. `/users/{userId}`: Student & admin profile docs. Student creates own profile; reads self or `isAppAdmin()`.
2. `/teachers/{teacherId}`: Institutional faculty roster. Readable by authenticated users; writable by `isAppAdmin()`.
3. `/assessments/{assessmentId}`: Generic assessments across 8 types. Read by authenticated users; create/update by `isTeacher()` or `isAppAdmin()`.
4. `/assessment_results/{resultId}`: Student test submissions. Created by student; read by student (own), teacher, or admin.
5. `/pending_mcqs/{mcqId}`: Gated questions awaiting teacher review. Read/write by `isTeacher()` or `isAppAdmin()`.
6. `/flashcards/{studentId}`: Student-owned flashcards; isolated by `uid == studentId` or `isAppAdmin()`.
7. `/learner_profiles/{studentId}`: BKT mastery states; isolated by `uid == studentId` or `isAppAdmin()`.
8. `/dialogue_states/{studentId}`: Conversation context states; isolated by `uid == studentId` or `isAppAdmin()`.
9. `/score_predictions/{studentId}`: Student prediction records; isolated by `uid == studentId` or `isAppAdmin()`.
10. `/chat_threads/{studentId}`: Tutor query threads; isolated by `uid == studentId` or `isAppAdmin()`.

### Rules Invariant:
- `isAppAdmin()`: Checks `request.auth.token.admin == true` or `/users/{uid}.role == "admin"`.
- `isTeacher()`: Checks `request.auth.token.role == "teacher"`, exists in `/teachers/{uid}`, or `/users/{uid}.role == "teacher"`.
- No sensitive collection allows unrestricted public write.

---

## 4. Authentication & Role Enforcement Baseline

### Role Hierarchy:
$$\text{SUPER\_ADMIN} > \text{TEACHER} > \text{STUDENT}$$

### Token & Identity Resolution:
1. `_header_identity()` extracts `Authorization: Bearer <token>`.
2. `_verify_firebase_token(token)` verifies cryptographically via Firebase Admin SDK.
3. Strict mode (`REQUIRE_FIREBASE_AUTH=true`): Fail-closed. Any invalid, missing, or mismatched token is rejected (401/403).
4. `resolve_user_role(uid, claims)`:
   - Claims `admin: true` or `role: "SUPER_ADMIN"` $\to$ `SUPER_ADMIN`.
   - `teacher_manager.is_teacher(uid)` or claims `role: "TEACHER"` $\to$ `TEACHER`.
   - Default fallback $\to$ `STUDENT`.

---

## 5. Assessment Engine Model Baseline (`assessment_engine.py`)

### 8 Generic Assessment Types:
1. `DAILY_TEST`
2. `WEEKLY_TEST`
3. `SATURDAY_TEST`
4. `CHAPTER_TEST`
5. `UNIT_TEST`
6. `MOCK_TEST`
7. `REVISION_TEST`
8. `CUSTOM_TEST`

### 6-Stage Strict Lifecycle State Machine:
$$\text{DRAFT} \to \text{PUBLISHED} \to \text{UPCOMING} \to \text{LIVE} \to \text{CLOSED} \to \text{RESULTS\_AVAILABLE}$$

### Security & Integrity Guardrails:
- Answer key scrubbing: Correct answers and explanations are stripped during `LIVE` exams.
- Duplicate submission lock: Prevents multi-attempt tampering.
- BKT Integration: Recorded test results automatically update student mastery vectors.

---

## 6. Frontend Architecture Baseline (`index.html` & `v2_ecosystem.js`)

### Current State:
- Monolithic Single Page Application (`index.html`) using DOM page switching:
  `go('home')`, `go('dashboard')`, `go('mcq')`, `go('ai-tutor')`, `go('teacher')`, `go('admin')`, etc.
- In-memory `DB` object storing session profile: `DB.currentUser`, `DB.userRole`, `DB.isAdmin`, `DB.isTeacher`.
- Unified `apiFetch` attaching Firebase ID tokens.
- Floating AI assistant (`#floatingAssistantWindow`) with persona switching bar:
  `[👩‍⚕️ Dr. Priya (Mentor)]  [👨‍🏫 Prof. Sharma (Faculty)]  [👑 Ops Advisor (Governance)]`.

### Shortcomings for V3:
1. All three portals currently share a single URL route structure (`/#dashboard`, `/#teacher`, `/#admin`).
2. There is no dedicated landing page directing visitors to their specific portal (`Student`, `Teacher`, `Admin`).
3. Navigation and layouts are mixed in one giant DOM instead of distinct, tailored portal experiences.
4. Portal separation currently relies on frontend DOM hides in addition to server gates, rather than dedicated portal entry points and distinct workspaces.

---

## 7. V3 Target Architecture Principles
1. **Zero Logic Duplication:** All three portals use the same underlying Firebase Auth, Firestore models, MCQ Engine, Adaptive Tutor, BKT Learner Model, and Assessment Engine.
2. **Dedicated Entry URLs:** Clean portal endpoints:
   - Student Portal: `/student` (or `students.bioneetpro.com`)
   - Teacher Portal: `/teacher` (or `teachers.bioneetpro.com`)
   - Admin Portal: `/admin` (or `admin.bioneetpro.com`)
   - Landing Page: `/` (or `bioneetpro.com`)
3. **Strict Server-Side Enforcement:** Backend verifies Firebase ID tokens on every protected route.
4. **Portal-Specific UI Identities:** Tailored layouts and metrics per persona.
5. **Preservation of 100% Existing Functionality:** V2 biology tests, AI tutor, and 108 existing tests must remain 100% green.
