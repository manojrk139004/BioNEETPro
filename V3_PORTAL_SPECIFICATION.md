# 📱 BioNEETPro V3 — Portal Specifications

This document outlines the detailed functional specifications, user experience flows, navigation hierarchies, and permitted features for all four application experiences in BioNEETPro V3.

---

## 1. 🧬 Central Ecosystem Gateway
- **Primary Domain:** `https://bioneetpro.com`
- **Fallback URL:** `/` or `http://localhost:5000/`
- **Target Audience:** All visitors, prospective students, educators, and institutional decision-makers.

### Core Features & Layout:
1. **Hero & 3D Interactive Visualizer:**
   - Interactive 3D biology canvas with real-time rotation.
   - Neumorphic quick statistics (38 Chapters, 6,600+ Questions, Live Student Counter).
2. **Ecosystem Portal Gateway Cards (`#portalGatewaySection`):**
   - **Student Learning Portal Card:** Highlights adaptive BKT, 6,600 MCQ bank, upcoming tests, and Dr. Priya AI Mentor.
   - **Teacher Assessment Studio Card:** Highlights AI wizard blueprinting, teacher review gating, class rosters, and Prof. Sharma AI Consultant.
   - **Super Admin Governance Console Card:** Highlights faculty provisioning, institutional rosters, system telemetry, and BioNEET Operations Advisor.
3. **Public Navigation Bar (`#gNav`):**
   - Links: Home, Features, Updates, Predictor, Leaderboard.
   - Action Buttons: `Log In` $\to$ `/student/login`, `Get Started →` $\to$ `/student/register`.

---

## 2. 🎓 Student Learning Portal
- **Primary Domain:** `https://students.bioneetpro.com`
- **Fallback URL:** `/student`, `/student/login`, `/student/dashboard`, etc.
- **Target Persona:** NEET UG Aspirants preparing for medical entrance examinations.
- **Visual Identity:** Fresh emerald accents (`#10b981`), motivational progress bars, streak meters, and gold badges.

### Core Features & Layout:
1. **Student Learning Dashboard (`#page-dashboard`):**
   - Personal greeting and target exam countdown (e.g. NEET 2026).
   - **Upcoming Institutional Tests Widget (`#studentUpcomingContainer`):** Real-time display of tests assigned by faculty. Allows one-click entry to live exams (`/student/assessment/take`).
   - Weak Chapter Radar: Direct links to practice low-mastery biology concepts.
2. **Mock Test & Practice Hall (`#page-mcq`):**
   - 6,600 verified NCERT questions with instant AI-driven step-by-step explanations.
   - Chapter-wise, unit-wise, and full-syllabus timed tests.
3. **Socratic AI Biology Mentor (`#page-ai-tutor`):**
   - Dr. Priya AI Mentor: Provides NCERT textbook citations, diagram descriptions, mnemonics, and exam trap warnings.
   - Interactive MCQ evaluation: Responds to answers with immediate conceptual feedback.
4. **Flashcards & NCERT Lesson Archives (`#page-flashcards`, `#page-lessons`):**
   - Spaced repetition Leitner-box review system for rapid memorization.
   - Curated video lectures from top NEET educators categorized by chapter.
5. **Score Predictor & Leaderboard (`#page-prediction`, `#page-leaderboard`):**
   - Bayesian Knowledge Tracing (BKT) score forecasting with college cutoffs.
   - National and institutional leaderboard rankings.
6. **Student Navigation Bar (`#sNav`):**
   - Links: Dashboard, Mock Test, AI Tutor, Flashcards, Lessons, Videos, Updates.
   - If user is elevated (Teacher/Admin), shows "Return to Teacher Studio" switcher button.

---

## 3. 👨‍🏫 Teacher Assessment Studio
- **Primary Domain:** `https://teachers.bioneetpro.com`
- **Fallback URL:** `/teacher`, `/teacher/login`, `/teacher/builder`, etc.
- **Target Persona:** Biology Faculty, Head of Departments, Coaching Instructors.
- **Visual Identity:** Academic indigo accents (`#4f46e5`), structured tables, blueprint builders, and diagnostic cards.

### Core Features & Layout:
1. **Teacher Assessments Studio (`#tViewAssessments`):**
   - Complete inventory of authored tests across all 8 assessment types (CHAPTER_PRACTICE, UNIT_TEST, FULL_SYLLABUS_MOCK, REVISION_QUIZ, DIAGNOSTIC_TEST, CHALLENGE_TEST, PYQ_ARCHIVE, SPEED_DRILL).
   - State transition controls: Move tests through `DRAFT` $\to$ `PUBLISHED` $\to$ `LIVE` $\to$ `CLOSED` $\to$ `RESULTS_AVAILABLE`.
2. **Assessment Builder & AI Wizard (`#tViewBuilder`):**
   - Cascading NCERT Class 11 & 12 curriculum selector (Class $\to$ Unit $\to$ Chapter).
   - **AI-Assisted Question Curation:** Generates targeted MCQs with configurable difficulty balancing (Easy 30%, Medium 50%, Hard 20%).
   - **Teacher Review Gating:** Questions remain in `PENDING_REVIEW` until faculty reviews, edits, and explicitly approves them.
3. **Results & Class Analytics (`#tViewAnalytics`):**
   - Roster submission tables with student scores, time spent, and submission timestamps.
   - Question-by-question diagnostic accuracy breakdown to pinpoint collective student misunderstandings.
4. **Dedicated Teacher Login (`#page-teacher-login`):**
   - Secure faculty authentication with email & password.
   - Cross-portal guardrail: Blocks students from logging in and redirects them to the Student Portal.
5. **Teacher Navigation Bar (`#tNav`):**
   - Links: My Assessments, Builder Wizard, Results & Analytics, Student View, AI Tutor.

---

## 4. 👑 Super Admin Governance Console
- **Primary Domain:** `https://admin.bioneetpro.com`
- **Fallback URL:** `/admin`, `/admin/login`, `/admin/teachers`, etc.
- **Target Persona:** School Principals, Institutional Directors, System Administrators.
- **Visual Identity:** Institutional slate & violet accents (`#0f172a`, `#7c3aed`), system telemetry grids, and security controls.

### Core Features & Layout:
1. **Platform Telemetry & Overview (`#page-admin`):**
   - Real-time registered student counts and score submission metrics.
   - Chapter-wise performance heatmaps and platform health status.
2. **Faculty Provisioning & Lifecycle (`#page-admin-teachers`):**
   - Onboard new faculty accounts with name, institutional email, phone, and department.
   - Status toggle: Immediately transition faculty status (`ACTIVE` $\leftrightarrow$ `INACTIVE` $\leftrightarrow$ `SUSPENDED`). Inactive accounts cannot author or publish tests.
   - Modify faculty profiles and permissions.
3. **Institutional Student Rosters (`#page-admin-students`):**
   - Searchable, sortable table of all enrolled students with target year, joined date, and performance history.
   - One-click CSV export of student performance records.
4. **Question Bank Quality Control (`#page-admin-mcq`):**
   - Central repository moderation across 6,600+ MCQs.
   - Delete or flag erroneous questions.
5. **System Announcements & Video Governance (`#page-admin-updates`, `#page-admin-videos`):**
   - Publish ecosystem-wide notices and manage curated video playlists.
6. **Dedicated Admin Login (`#page-admin-login`):**
   - Super admin authentication gate with fail-closed security.
7. **Admin Navigation Bar (`#aNav`):**
   - Links: Overview, Teachers, Teacher Portal, Students, MCQs, Videos, Updates.
