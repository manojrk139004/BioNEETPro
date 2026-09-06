# 🧬 BioNEETPro V2 — API Documentation

## Authentication & Authorization

All protected endpoints require either:
1. Standard Firebase ID token in `Authorization: Bearer <token>` header, or
2. `X-Dev-Role: SUPER_ADMIN | TEACHER | STUDENT` (when running in `DEV_AUTH_MODE=true`).

Every endpoint fails closed with `401 Unauthorized` (missing/invalid token) or `403 Forbidden` (insufficient role privileges).

---

## 1. Authentication & Profile

### `GET /api/auth/me`
Retrieves current authenticated identity, resolved institutional role, and profile details.
- **Required Role**: Any authenticated user (`STUDENT`, `TEACHER`, `SUPER_ADMIN`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "user": {
    "uid": "teacher_123",
    "email": "teacher@school.edu",
    "displayName": "Dr. Sunita Rao",
    "role": "TEACHER",
    "teacher_profile": {
      "id": "teacher_123",
      "department": "Botany",
      "status": "ACTIVE"
    }
  }
}
```

---

## 2. Institutional Teacher Management (Admin Only)

### `GET /api/admin/teachers`
Lists all institutional faculty accounts with optional status filtering.
- **Required Role**: `SUPER_ADMIN`
- **Query Parameters**: `status=ACTIVE|INACTIVE` (optional)
- **Response (200 OK)**:
```json
{
  "success": true,
  "count": 2,
  "teachers": [
    {
      "id": "teacher_01",
      "name": "Dr. Sunita Rao",
      "email": "sunita@bioneet.edu",
      "department": "Botany",
      "status": "ACTIVE"
    }
  ]
}
```

### `POST /api/admin/teachers`
Provisions a new teacher profile and Firebase auth account.
- **Required Role**: `SUPER_ADMIN`
- **Request Body**:
```json
{
  "name": "Prof. R. K. Verma",
  "email": "verma@bioneet.edu",
  "password": "SecurePassword123!",
  "department": "Zoology",
  "subjects": ["Class 12 Human Reproduction", "Genetics"],
  "phone": "+91-9876543210"
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "teacher": {
    "id": "teacher_xyz",
    "name": "Prof. R. K. Verma",
    "email": "verma@bioneet.edu",
    "status": "ACTIVE",
    "role": "TEACHER"
  }
}
```

### `PATCH /api/admin/teachers/<teacher_id>/status`
Toggles teacher status between `ACTIVE` and `INACTIVE`.
- **Required Role**: `SUPER_ADMIN`
- **Request Body**: `{"status": "INACTIVE"}`
- **Response (200 OK)**:
```json
{
  "success": true,
  "new_status": "INACTIVE",
  "teacher": { "id": "teacher_xyz", "status": "INACTIVE" }
}
```

### `PUT /api/admin/teachers/<teacher_id>`
Modifies teacher profile details (department, subjects, phone, name).
- **Required Role**: `SUPER_ADMIN`
- **Request Body**:
```json
{
  "name": "Prof. R. K. Verma, Ph.D.",
  "department": "Senior Faculty - Zoology"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "teacher": { "id": "teacher_xyz", "name": "Prof. R. K. Verma, Ph.D." }
}
```

---

## 3. Canonical Curriculum

### `GET /api/curriculum`
Fetches the 33 canonical rationalized NCERT Biology chapters structured in a 2-level cascading hierarchy.
- **Required Role**: Public / Any authenticated user
- **Response (200 OK)**:
```json
{
  "success": true,
  "total_chapters": 33,
  "classes": [
    {
      "id": "class_11",
      "name": "Class 11",
      "units": [
        {
          "id": "unit_1",
          "name": "Diversity in the Living World",
          "chapters": [
            { "id": "c01", "name": "The Living World" },
            { "id": "c02", "name": "Biological Classification" },
            { "id": "c03", "name": "Plant Kingdom" },
            { "id": "c04", "name": "Animal Kingdom" }
          ]
        }
      ]
    }
  ]
}
```

---

## 4. Assessment Engine & Exam Workflows

### `POST /api/assessments`
Creates a new scheduled or draft assessment.
- **Required Role**: `TEACHER` or `SUPER_ADMIN`
- **Request Body**:
```json
{
  "title": "Class 11 Cell Biology Weekly Test",
  "type": "WEEKLY_TEST",
  "class_id": "class_11",
  "chapter_id": "c08",
  "chapter_name": "Cell: The Unit of Life",
  "duration_minutes": 30,
  "total_marks": 40,
  "passing_marks": 16,
  "negative_marking": true,
  "start_at": "2026-09-07T10:00:00Z",
  "end_at": "2026-09-07T11:00:00Z",
  "questions": [ /* Array of MCQs */ ],
  "status": "DRAFT"
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "assessment": {
    "id": "asmt_123",
    "status": "DRAFT",
    "title": "Class 11 Cell Biology Weekly Test"
  }
}
```

### `GET /api/assessments`
Lists assessments filtered by role and status.
- **Rules**:
  - `STUDENT`: `DRAFT` assessments are strictly filtered out; answers and explanations stripped.
  - `TEACHER`: Defaults to tests created by the calling teacher.
- **Query Parameters**: `status`, `type`, `class_id`, `chapter_id`, `all=true`
- **Response (200 OK)**:
```json
{
  "success": true,
  "count": 5,
  "assessments": [ /* Array of Assessment Objects */ ]
}
```

### `GET /api/assessments/upcoming`
Dedicated endpoint returning tests in `UPCOMING`, `LIVE`, or `PUBLISHED` states for student dashboard notifications.
- **Required Role**: Any authenticated user (typically `STUDENT`)
- **Response (200 OK)**:
```json
{
  "success": true,
  "count": 2,
  "upcoming_assessments": [
    {
      "id": "asmt_123",
      "title": "Class 11 Cell Biology Weekly Test",
      "status": "LIVE",
      "duration_minutes": 30,
      "start_at": "2026-09-06T12:00:00Z",
      "has_submitted": false
    }
  ]
}
```

### `GET /api/assessments/<assessment_id>`
Retrieves assessment details and question paper.
- **Security Guardrail**: Answers (`correct_index`, `correct_answer`, `explanation`) are completely stripped unless role is `TEACHER`/`SUPER_ADMIN` or test status is `RESULTS_AVAILABLE`.
- **Response (200 OK)**:
```json
{
  "success": true,
  "assessment": {
    "id": "asmt_123",
    "title": "Class 11 Cell Biology Weekly Test",
    "status": "LIVE",
    "questions": [
      {
        "id": "q1",
        "question": "Which organelle is the powerhouse?",
        "options": ["Ribosome", "Mitochondria", "Golgi", "Lysosome"]
      }
    ]
  }
}
```

### `POST /api/assessments/<assessment_id>/status`
Transitions assessment through its 6-stage lifecycle (`DRAFT` -> `PUBLISHED` -> `CLOSED` -> `RESULTS_AVAILABLE`).
- **Required Role**: Creator `TEACHER` or `SUPER_ADMIN`
- **Request Body**: `{"status": "PUBLISHED"}`
- **Response (200 OK)**:
```json
{
  "success": true,
  "new_status": "PUBLISHED"
}
```

### `POST /api/assessments/<assessment_id>/submit`
Submits student answers for grading and BKT model synchronization.
- **Required Role**: `STUDENT`
- **Single Submission Guardrail**: Second submission attempt returns `400 Bad Request`.
- **Request Body**:
```json
{
  "answers": { "0": 1, "1": 0 },
  "time_spent_seconds": 180
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "score": 8,
  "total_marks": 8,
  "percentage": 100.0,
  "correct_count": 2,
  "incorrect_count": 0,
  "unattempted_count": 0
}
```

### `GET /api/assessments/<assessment_id>/my-result`
Retrieves personal submission result, score, accuracy, and rank.
- **Required Role**: `STUDENT`
- **Response (200 OK)**:
```json
{
  "success": true,
  "result": {
    "score": 8,
    "percentage": 100.0,
    "correct": 2,
    "incorrect": 0,
    "timeSpentSeconds": 180
  }
}
```

### `GET /api/assessments/<assessment_id>/results`
Retrieves class-wide roster, ranked leaderboard, score statistics, and question accuracy analysis.
- **Required Role**: Creator `TEACHER` or `SUPER_ADMIN`
- **Response (200 OK)**:
```json
{
  "success": true,
  "statistics": {
    "total_submissions": 24,
    "highest_score": 76,
    "lowest_score": 12,
    "average_score": 54.2
  },
  "question_analysis": [
    {
      "question_index": 0,
      "question": "Which organelle is the powerhouse?",
      "correct_count": 22,
      "incorrect_count": 2,
      "accuracy": 91.7
    }
  ],
  "results": [ /* Ranked submission array */ ]
}
```

---

## 5. AI Question Curation & Review Gating

### `POST /api/mcqs/ai-generate`
Curates NEET MCQs using textbook retrieval and LLM matching.
- **Required Role**: `TEACHER` or `SUPER_ADMIN`
- **Request Body**:
```json
{
  "chapter": "Cell: The Unit of Life",
  "topic": "Endomembrane System",
  "difficulty": "medium",
  "count": 5
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "count": 5,
  "review_required": true,
  "questions": [
    {
      "id": "gen_mcq_123",
      "question": "Which structure...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "correct_answer": "A",
      "status": "PENDING_REVIEW",
      "is_ai_generated": true
    }
  ]
}
```

### `POST /api/mcqs/approve`
Teacher review gating gatekeeper. Validates questions and transitions them to `APPROVED`.
- **Required Role**: `TEACHER` or `SUPER_ADMIN`
- **Request Body**:
```json
{
  "questions": [ /* Array of questions reviewed by teacher */ ]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "approved_count": 5,
  "approved_questions": [ /* Approved questions */ ]
}
```

---

## 6. Multi-Role AI Assistant

### `POST /api/assistant/chat`
Universal floating assistant with persona switching and injection safety.
- **Required Role**: Any authenticated user
- **Request Body**:
```json
{
  "message": "Explain the stages of Meiosis I",
  "history": [ /* Optional history */ ],
  "context": { "page": "assessment_take" }
}
```
- **Response (200 OK)**:
```json
{
  "status": "success",
  "role": "STUDENT",
  "reply": "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n📌 **Meiosis I: Reductional Division**\n...",
  "mode": "ai_assistant_online"
}
```
- **Hostile Prompt Injection Attempt Response (200 OK)**:
```json
{
  "status": "rejected",
  "reply": "I am strictly programmed to assist with verified NCERT Biology education and assessment workflows."
}
```
