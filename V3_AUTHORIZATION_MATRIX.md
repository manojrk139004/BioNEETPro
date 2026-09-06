# 🔐 BioNEETPro V3 — Authorization Matrix & Security Specification

## 1. Role Hierarchy
BioNEETPro V3 implements a strict three-tier role hierarchy:

$$\text{SUPER\_ADMIN} \succ \text{TEACHER} \succ \text{STUDENT}$$

- **`SUPER_ADMIN`**: Institutional administrator with unrestricted governance privileges across all three portals, faculty provisioning, student rosters, and system telemetry.
- **`TEACHER`**: Faculty member with access to assessment authoring, AI question generation, question review gating, and student class analytics. Also permitted to view the student interface.
- **`STUDENT`**: Medical aspirant with access strictly limited to the Student Learning Portal, practice engines, live exam hall, and Dr. Priya AI Mentor.

---

## 2. Server-Side API Endpoint Access Matrix

| Endpoint Category | Method & Path | GUEST | STUDENT | TEACHER | SUPER_ADMIN | Enforcement Mechanism |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Public Gateway** | `GET /` | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 | Public entry route |
| **Student Entry** | `GET /student/*` | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 | Serves frontend bootstrap |
| **Teacher Entry** | `GET /teacher/*` | ✅ 200 | ⚠️ Gated | ✅ 200 | ✅ 200 | Client-side role redirect |
| **Admin Entry** | `GET /admin/*` | ✅ 200 | ⛔ Gated | ⛔ Gated | ✅ 200 | Client-side role redirect |
| **Auth Verification** | `GET /api/auth/me` | ⛔ 401 | ✅ 200 | ✅ 200 | ✅ 200 | Firebase ID Token / Claims |
| **Curriculum** | `GET /api/curriculum` | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 | Public syllabus data |
| **AI Question Gen** | `POST /api/mcqs/ai-generate` | ⛔ 401 | ⛔ 403 | ✅ 200 | ✅ 200 | Role verification check |
| **MCQ Review Approval**| `POST /api/mcqs/approve` | ⛔ 401 | ⛔ 403 | ✅ 200 | ✅ 200 | Teacher review gate |
| **Create Assessment** | `POST /api/assessments` | ⛔ 401 | ⛔ 403 | ✅ 200 | ✅ 200 | Role verification check |
| **List Assessments** | `GET /api/assessments` | ⛔ 401 | ⛔ 403 | ✅ 200 | ✅ 200 | Teacher/Admin filter |
| **Upcoming Tests** | `GET /api/assessments/upcoming`| ⛔ 401 | ✅ 200 | ✅ 200 | ✅ 200 | Verified student session |
| **Live Exam Taking** | `GET /api/assessments/<id>` | ⛔ 401 | ✅ 200* | ✅ 200 | ✅ 200 | *Answer key stripped for students |
| **Submit Assessment** | `POST /api/assessments/<id>/submit`| ⛔ 401| ✅ 200 | ⛔ 400 | ⛔ 400 | One submission lock per student |
| **Personal Result** | `GET /api/assessments/<id>/my-result`| ⛔ 401| ✅ 200 | ✅ 200 | ✅ 200 | Scoped to caller UID |
| **Class Analytics** | `GET /api/assessments/<id>/results` | ⛔ 401| ⛔ 403 | ✅ 200 | ✅ 200 | Teacher/Admin only |
| **Faculty Mgmt** | `GET,POST /api/admin/teachers` | ⛔ 401 | ⛔ 403 | ⛔ 403 | ✅ 200 | Fail-closed admin check |
| **Faculty Status** | `PATCH /api/admin/teachers/<id>/status`| ⛔ 401| ⛔ 403 | ⛔ 403 | ✅ 200 | Fail-closed admin check |
| **Floating AI Chat** | `POST /api/assistant/chat` | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 | Contextual persona scoping |

---

## 3. Cross-Portal Login Guardrails

When a user attempts to log in using an unsuited portal interface, the system intercepts the session and guides the user safely:

```
                                  USER LOGS IN
                                       │
                     ┌─────────────────┴─────────────────┐
                     ▼                                   ▼
             Teacher Login                       Admin Login
          (#page-teacher-login)               (#page-admin-login)
                     │                                   │
         Is user role == STUDENT?             Is role != SUPER_ADMIN?
         ┌───────────┴───────────┐           ┌───────────┴───────────┐
         ▼                       ▼           ▼                       ▼
       YES                       NO         YES                      NO
        │                        │           │                       │
 ⛔ Show Alert:           ✅ Access Granted: ⛔ Show Alert:       ✅ Access Granted:
 "Student Account         Welcome to        "Access Denied:       Welcome to
 Detected. Redirecting    Teacher Studio!   Admin credentials     Governance Console!
 to Student Portal..."                      required."
        │                                    │
 🔄 Auto-redirect                            🔄 Sign out & redirect
 to /student                                 to appropriate portal
```

### 3.1 Student Login via Teacher Portal (`/teacher/login`)
- **Detection:** `doTeacherLogin()` inspects verified role from `loadUserProfile(cred.user)`.
- **Action:**
  1. Signs out user immediately from privileged session context.
  2. Displays warning toast: `⚠️ Student account detected! Please log in via the Student Portal.`
  3. Seamlessly redirects to `V3.navigateToPortal('STUDENT')` after 1.5 seconds.

### 3.2 Non-Admin Login via Admin Portal (`/admin/login`)
- **Detection:** `doAdminLogin()` validates `role === 'SUPER_ADMIN' || role === 'ADMIN'`.
- **Action:**
  1. Blocks login and signs out user.
  2. Displays alert toast: `⛔ Access Denied: Institutional Super Admin credentials required.`
  3. No privilege escalation is possible.

---

## 4. Assessment Integrity Guardrails
1. **Concealment of Draft Assessments:**
   - Unreleased tests (`DRAFT`, `SCHEDULED` prior to start window) are completely filtered out from student endpoints.
2. **Answer Key Scrubbing:**
   - When a student fetches a live assessment via `/api/assessments/<id>`, all `correct_index` and `explanation` attributes are recursively removed from the response payload on the server.
3. **Duplicate Submission Locking:**
   - Once an assessment submission is received for a student, any subsequent attempt returns HTTP 400: `You have already submitted this assessment. Duplicate submissions are not allowed.`
4. **Time Window Gating:**
   - Submissions outside the assessment window (`window_start` to `window_end` plus grace period) are rejected.
