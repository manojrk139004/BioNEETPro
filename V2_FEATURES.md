# 🧬 BioNEETPro V2 — Feature Documentation & Architecture Specification

## Overview

BioNEETPro V2 transforms the platform from an individual student biology revision app into a complete **Institutional School & College Assessment Ecosystem** while preserving 100% of the original V1 foundations (6,600 verified MCQs, 33 NCERT chapters, Dr. Priya AI Tutor, RAG pipeline, and BKT adaptive learner model).

---

## 1. Multi-Role Institutional Hierarchy

BioNEETPro V2 enforces a strict three-tier role-based access control (RBAC) hierarchy:

```
                  ┌───────────────────────────────┐
                  │    👑 SUPER_ADMIN (Admin)     │
                  │ Institution Admin / Principal │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │      👨‍🏫 TEACHER (Faculty)     │
                  │   Biology Dept Educators      │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │      🎓 STUDENT (Learner)     │
                  │   NEET Medical Aspirants      │
                  └───────────────────────────────┘
```

### Role Capabilities
- **`SUPER_ADMIN`**: Full platform authority. Can provision teachers, toggle status (`ACTIVE` / `INACTIVE`), modify teacher metadata, view platform-wide audit trails, supervise all assessments across teachers, and access institutional operations.
- **`TEACHER`**: Assessment authoring, AI-assisted question curation with review gating, assessment scheduling across 8 types, lifecycle management (DRAFT -> PUBLISHED -> LIVE -> CLOSED -> RESULTS_AVAILABLE), and class roster analytics.
- **`STUDENT`**: AI tutor interactions (Dr. Priya), practice quizzes, flashcards, diagnostic mock tests, viewing scheduled/upcoming institutional tests, sitting live exams in the proctored-style test hall, and reviewing personal results and question breakdowns.

---

## 2. Institutional Teacher Management System

The Main Administrator portal (`#page-admin-teachers`) provides institutional governance:
- **Teacher Account Provisioning**: Admins create faculty profiles with institutional email, department (Botany / Zoology), subject allocations, and credentials.
- **Immediate Status Revocation**: One-click toggling between `ACTIVE` and `INACTIVE`. When marked `INACTIVE`, Firebase authentication is disabled, and subsequent API calls fail closed.
- **Faculty Roster Search & Filter**: Filter teachers by department, active status, or subject specialty.

---

## 3. Generic Assessment Engine

A unified engine powers institutional assessments:

### Supported Assessment Types (8 Types)
1. **`DAILY_TEST`**: 10-15 questions for daily classroom exit-tickets.
2. **`WEEKLY_TEST`**: 20-30 questions testing the week's biological concepts.
3. **`SATURDAY_TEST`**: High-yield weekend milestone assessments.
4. **`CHAPTER_TEST`**: Rigorous chapter-level testing from canonical NCERT chapters.
5. **`UNIT_TEST`**: Multi-chapter tests spanning an entire NCERT Unit (e.g. Unit 3: Cell Structure & Function).
6. **`MOCK_TEST`**: Full-length 45-90 question simulated NEET papers.
7. **`REVISION_TEST`**: Targeted remediation tests focused on high-frequency error concepts.
8. **`CUSTOM_TEST`**: Teacher-curated flexible assessments.

### Strict 6-Stage Lifecycle State Machine
```
[ DRAFT ] ──> [ PUBLISHED ] ──> [ UPCOMING ] ──> [ LIVE ] ──> [ CLOSED ] ──> [ RESULTS_AVAILABLE ]
   │               │                                 │
   └───────────────┴─────────────────────────────────┘
                   (Can transition to CLOSED)
```

- **`DRAFT`**: Authoring state. Questions and settings can be edited. Strictly invisible to students.
- **`PUBLISHED`**: Scheduled and locked. Becomes visible in student Upcoming Tests with live countdown.
- **`UPCOMING`**: Dynamic state when current timestamp is before `start_at`.
- **`LIVE`**: Active window (`start_at <= now <= end_at`). Students can enter the exam taking hall.
- **`CLOSED`**: Window has elapsed. Submissions rejected (subject to a 5-minute network grace period).
- **`RESULTS_AVAILABLE`**: Teacher releases answer keys, ranked leaderboard, and student scorecards.

---

## 4. Canonical NCERT Chapter Selection (Cascading Hierarchy)

To eliminate free-text errors and syllabus drift, V2 introduces a canonical two-level cascading hierarchy:
- **Class 11** (5 Units, 19 Chapters):
  - Unit 1: Diversity in the Living World (Chapters c01-c04)
  - Unit 2: Structural Organisation in Animals and Plants (Chapters c05-c07)
  - Unit 3: Cell Structure and Function (Chapters c08-c10)
  - Unit 4: Plant Physiology (Chapters c13-c15)
  - Unit 5: Human Physiology (Chapters c16-c22)
- **Class 12** (5 Units, 14 Chapters):
  - Unit 6: Reproduction (Chapters c23-c25)
  - Unit 7: Genetics and Evolution (Chapters c26-c28)
  - Unit 8: Biology in Human Welfare (Chapters c29-c30)
  - Unit 9: Biotechnology (Chapters c31-c32)
  - Unit 10: Ecology and Environment (Chapters c33-c35)

Teachers select Class -> Unit -> Chapter via linked dropdowns. The server verifies chapter IDs against `get_canonical_curriculum()`, rejecting non-biology or unapproved inputs.

---

## 5. AI-Assisted Assessment Creation & Review Gating

Teachers can generate tailored NEET questions on demand:
1. **Teacher Request**: Specifies canonical chapter, topic, target difficulty (Easy / Medium / Hard), and count.
2. **Draft Generation**: Engine curates matching MCQs with `status: "PENDING_REVIEW"` and `is_ai_generated: True`.
3. **Review Gating**: AI questions cannot be assigned to an assessment until a teacher reviews the question stem, options, correct index, and explanation, and explicitly calls `/api/mcqs/approve`.
4. **Validation Check**: `mcq_engine.validate_mcq` verifies 4 unique options, valid 0-3 answer index, and exact option match.

---

## 6. Student Assessment Taking Hall & Upcoming Tests

- **Upcoming Tests Dashboard Card**: Embedded directly on the student home view (`#page-dashboard`), displaying upcoming tests with real-time countdown timers, duration, question count, and dynamic "Enter Exam" action when live.
- **Live Exam Hall (`#page-assessment-take`)**:
  - Distraction-free full-screen test environment.
  - Floating live countdown timer with auto-submit warning when 2 minutes remain.
  - Interactive Question Palette (palette buttons indicate Attempted, Current, and Unanswered).
  - Clear Question & Options display with radio selection.
  - Time-spent tracking per session.
- **Answer Key Security**: When a student fetches a test during the `LIVE` window, `correct_index`, `correct_answer`, and `explanation` are completely scrubbed server-side before JSON serialization.
- **Duplicate Submission Lock**: Students are restricted to exactly one submission per assessment (`res_<asmt_id>_<student_id>`). Second attempts return HTTP 400.

---

## 7. NEET Scoring & Adaptive BKT Integration

- **Standard NEET Marking**: Evaluates submissions with `+4` marks for each correct choice, `-1` mark for incorrect answers (when `negative_marking: true`), and `0` for unattempted questions.
- **Bayesian Knowledge Tracing (BKT)**: Every question response updates the student's latent mastery probability $P(L_t)$ in `learner_profiles` across concept nodes (e.g. `BIO-C08-MITO`).
- **Personal Result View**: Students inspect their score, accuracy percentage, time taken, and rank once results are published.

---

## 8. Teacher Assessment Analytics & Leaderboard

Teachers access class performance metrics via `/api/assessments/<id>/results`:
- Total submissions and participation rate.
- Score distribution (Highest, Lowest, Average).
- Ranked Student Leaderboard with time-taken tie-breaking.
- Question-Level Accuracy Analysis (computes percentage accuracy and identifying tricky distractor options).

---

## 9. Global Floating AI Assistant Widget

An institutional floating assistant (`#floatingAssistantWindow`) is accessible from any page, dynamically adapting to the user's active role:
- **Student Persona (Dr. Priya)**: NEET Biology Tutor. Explains biological concepts, provides diagrams, alerts on exam traps, and checks syllabus boundaries.
- **Teacher Persona (Prof. Sharma)**: Assessment Specialist. Guides question balancing (30% Easy, 50% Medium, 20% Hard), MCQ structuring, and remediation advice.
- **Admin Persona (Operations Advisor)**: Institutional Advisor. Explains teacher provisioning, security rules, audit logs, and platform policies.
- **Injection Defense**: Uses strict regex-based and semantic guardrails to reject prompt injections ("ignore previous instructions", "DAN", etc.) with `status: "rejected"`.
- **Hybrid Architecture**: Leverages OpenRouter LLM with automated fallback to verified local NCERT retrieval when offline or during network latency.
