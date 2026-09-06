# 🧬 BioNEETPro V3 — Multi-Portal Product Architecture

## 1. Executive Summary & Master Vision
BioNEETPro V3 transforms the completed V2 platform into an enterprise-grade, multi-portal educational ecosystem designed specifically for the rigorous demands of NEET UG Biology preparation.

Rather than fragmenting into three disconnected codebases or duplicating business logic, BioNEETPro V3 employs a **Unified Core Engine Architecture**:
- 🎓 **Student Portal** (`/student` or `students.bioneetpro.com`): Self-paced NCERT mastery, adaptive BKT practice, mock tests, live scheduled institutional exams, and Dr. Priya AI Mentor.
- 👨‍🏫 **Teacher Portal** (`/teacher` or `teachers.bioneetpro.com`): Institutional assessment authoring, AI question generation with teacher review gating, student rosters, diagnostic analytics, and Prof. Sharma AI Consultant.
- 👑 **Super Admin Portal** (`/admin` or `admin.bioneetpro.com`): Institutional governance, faculty provisioning & lifecycle management, student rosters, real-time platform health telemetry, and BioNEET Operations Advisor.
- 🧬 **Ecosystem Landing Gateway** (`/` or `bioneetpro.com`): Central portal discovery and routing gateway.

```
                         BioNEETPro V3 Unified Ecosystem
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   🎓 Student Portal            👨‍🏫 Teacher Portal          👑 Super Admin Portal
   /student                     /teacher                     /admin
   students.bioneetpro.com      teachers.bioneetpro.com      admin.bioneetpro.com
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        │
                         SHARED ZERO-DUPLICATION CORE
      ┌─────────────────────────────────┴─────────────────────────────────┐
      │  • Firebase Authentication (Verified JWT ID Tokens & Custom Claims)│
      │  • Firestore Multi-Collection Store (users, assessments, mcqs)    │
      │  • 6,600 Verified NCERT MCQ Question Bank                        │
      │  • Bayesian Knowledge Tracing (BKT) Learner Engine                 │
      │  • Adaptive Biology Socratic Dialog Engine                        │
      │  • Canonical Class 11 & 12 Curriculum Hierarchy (33 Chapters)    │
      │  • Assessment Lifecycle & Real-Time Exam Window State Machine    │
      └───────────────────────────────────────────────────────────────────┘
```

---

## 2. Shared Core Invariant
All portals communicate with the exact same backend engine:
1. **Single Database / Shared Persistence:**
   - User identity is universal: A student account exists in the unified `users` collection.
   - Teachers are registered in `teachers` collection with institutional affiliation.
   - Assessments authored by a teacher in `/teacher` immediately reflect in `/student/assessments/upcoming` for enrolled students once published.
2. **Zero Logic Duplication:**
   - The assessment scoring engine (+4/-1 NEET marking, duplicate submission locking, answer key scrubbing during live tests) serves both students and teachers.
   - The 6,600 verified MCQ question bank is queried identically whether a student is taking an adaptive test or a teacher is auto-generating assessment drafts.
   - The Bayesian Knowledge Tracing (BKT) model continuously updates learner mastery regardless of whether practice occurred during self-study or teacher-assigned exams.
3. **HTML Byte-for-Byte Parity:**
   - `index.html` and `BioNeet-Pro.html` remain strictly 100% byte-for-byte identical (validated via SHA-256 hash `CA2828FB83378EABAFCD4C5034B762DABC3BDC39BD5EF5415927FA418668243D`).

---

## 3. Dual-Mode URL Architecture & Routing

### 3.1 Hostname Subdomain Routing (Production)
In cloud production, DNS CNAME records route specialized subdomains to the platform:
- `students.bioneetpro.com` $\to$ Automatically activates Student Portal.
- `teachers.bioneetpro.com` $\to$ Automatically activates Teacher Portal.
- `admin.bioneetpro.com` $\to$ Automatically activates Super Admin Portal.
- `bioneetpro.com` $\to$ Activates Ecosystem Landing Gateway.

### 3.2 Path-Based Routing (Local Development & Direct Linking)
To guarantee zero-friction local development (`http://localhost:5000`) and cloud previews without requiring manual DNS configuration:
- `http://localhost:5000/` $\to$ Ecosystem Landing Gateway
- `http://localhost:5000/student` $\to$ Student Portal
- `http://localhost:5000/teacher` $\to$ Teacher Portal
- `http://localhost:5000/admin` $\to$ Super Admin Portal

### 3.3 Client-Side Router (`v3_portal_router.js`)
The zero-dependency client router manages routing state:
```javascript
// Detects active portal from hostname (production) or pathname (local/fallback)
var portal = V3.detectPortal();

// Evaluates user role and enforces portal boundaries
V3.syncPortalAuth();

// Aligns floating AI Assistant persona to current portal context
V3.alignAIAssistantPersona();
```

---

## 4. Server-Side Route Architecture (`app.py`)

### 4.1 Dedicated Entry Route Handlers
`app.py` exposes dedicated route decorators that serve the application for all portal URLs:
```python
@app.get("/")
@app.get("/student")
@app.get("/student/")
@app.get("/student/<path:subpath>")
@app.get("/teacher")
@app.get("/teacher/")
@app.get("/teacher/<path:subpath>")
@app.get("/admin")
@app.get("/admin/")
@app.get("/admin/<path:subpath>")
def serve_portal_entry(subpath=None):
    """Serve the BioNEET Pro web frontend for root and all dedicated portal routes."""
    for name in ("index.html", "BioNeet-Pro.html"):
        index_file = BASE_DIR / name
        if index_file.exists():
            return send_file(index_file)
    return health()
```

### 4.2 Subpath Asset Fallback
`serve_root_asset` ensures that static assets requested from subpath URLs (e.g. `/student/v3_portals.css` or `/teacher/v2_ecosystem.js`) resolve correctly to `BASE_DIR` without generating 404 errors, while unknown `/api/` endpoints strictly return 404 JSON.

### 4.3 Server-Side Portal Decorators
```python
@require_student_portal  # Permits STUDENT, TEACHER, SUPER_ADMIN
@require_teacher_portal  # Permits TEACHER, SUPER_ADMIN (Blocks STUDENT with 403)
@require_admin_portal    # Permits SUPER_ADMIN (Blocks STUDENT and TEACHER with 403)
```

---

## 5. Contextual AI Assistant Persona Architecture
The floating AI Assistant widget (`#floatingAssistantWidget`) dynamically adopts portal-specific pedagogical and operational personas:

| Portal Context | Persona Name | Role Identity | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Student Portal** | Dr. Priya | NEET Biology Mentor | Explaining NCERT concepts, diagrams, mnemonics, exam traps, and evaluating student MCQ answers. |
| **Teacher Portal** | Prof. Sharma | Academic Assessment Specialist | Assisting faculty in blueprinting tests, balancing difficulty (30/50/20 ratio), and interpreting class diagnostic metrics. |
| **Super Admin Portal** | BioNEET Operations | Institutional Systems Advisor | Advising administrators on teacher onboarding protocols, security audit logs, and platform health telemetry. |

**Data Isolation & Academic Guardrails:**
- If a user submits an MCQ answer (`Q1: A`), it is always graded by Dr. Priya.
- Prompt injection attempts (e.g., DAN jailbreaks, instruction overrides) are rejected with HTTP 200/rejected status.
- Strict data isolation prevents students from extracting live exam answer keys or institutional audit credentials.
