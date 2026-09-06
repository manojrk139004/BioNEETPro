"""
BioNEETPro V2 — Unified Assessment Engine
Manages Generic Assessments across 8 types, strict 6-stage lifecycle,
time guards, scoring, duplicate submission locks, and BKT adaptive learner integration.
"""

import datetime
from datetime import timezone
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
import firestore_store
from learner_model import learner_manager

ASSESSMENT_TYPES = [
    "DAILY_TEST",
    "WEEKLY_TEST",
    "SATURDAY_TEST",
    "CHAPTER_TEST",
    "UNIT_TEST",
    "MOCK_TEST",
    "REVISION_TEST",
    "CUSTOM_TEST"
]

LIFECYCLE_STATES = [
    "DRAFT",
    "PUBLISHED",
    "UPCOMING",
    "LIVE",
    "CLOSED",
    "RESULTS_AVAILABLE"
]

ALLOWED_TRANSITIONS = {
    "DRAFT": {"PUBLISHED", "CLOSED"},
    "PUBLISHED": {"UPCOMING", "LIVE", "CLOSED", "DRAFT"},
    "UPCOMING": {"LIVE", "CLOSED"},
    "LIVE": {"CLOSED", "RESULTS_AVAILABLE"},
    "CLOSED": {"RESULTS_AVAILABLE", "LIVE"},
    "RESULTS_AVAILABLE": set()
}

GRACE_PERIOD_MINUTES = 5


def _iso_now() -> str:
    return datetime.datetime.now(timezone.utc).isoformat()


def _parse_iso(iso_str: Optional[str]) -> Optional[datetime.datetime]:
    if not iso_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _sanitize_question_for_student(q: Dict[str, Any]) -> Dict[str, Any]:
    q_copy = dict(q)
    q_copy.pop("correct", None)
    q_copy.pop("correct_index", None)
    q_copy.pop("correct_answer", None)
    q_copy.pop("answer", None)
    q_copy.pop("expl", None)
    q_copy.pop("explanation", None)
    return q_copy


class AssessmentEngine:
    def __init__(self):
        pass

    def compute_dynamic_status(self, asmt: Dict[str, Any]) -> str:
        current_status = str(asmt.get("status", "DRAFT")).upper()
        if current_status in ("DRAFT", "CLOSED", "RESULTS_AVAILABLE"):
            return current_status

        now = datetime.datetime.now(timezone.utc)
        start_at = _parse_iso(asmt.get("start_at") or asmt.get("startAt"))
        end_at = _parse_iso(asmt.get("end_at") or asmt.get("endAt"))

        if start_at and now < start_at:
            return "UPCOMING"
        if start_at and end_at:
            if start_at <= now <= end_at:
                return "LIVE"
            if now > end_at:
                return "CLOSED"
        elif start_at and now >= start_at:
            return "LIVE"

        return current_status

    def create_assessment(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Creates an assessment record. Supports:
        create_assessment(data, creator_uid=..., role=...)
        create_assessment(creator_uid, creator_name, data)
        """
        if len(args) == 3 and isinstance(args[0], str) and isinstance(args[2], dict):
            creator_uid = args[0]
            creator_name = args[1]
            data = args[2]
            role = kwargs.get("role", "TEACHER")
        elif len(args) >= 1 and isinstance(args[0], dict):
            data = args[0]
            creator_uid = kwargs.get("creator_uid", "teacher_local")
            creator_name = kwargs.get("creator_name", "Teacher")
            role = kwargs.get("role", "TEACHER")
        else:
            data = kwargs.get("data") or {}
            creator_uid = kwargs.get("creator_uid", "teacher_local")
            creator_name = kwargs.get("creator_name", "Teacher")
            role = kwargs.get("role", "TEACHER")

        title = str(data.get("title") or "").strip()
        asmt_type = str(data.get("type") or "CUSTOM_TEST").strip().upper()
        subject = str(data.get("subject") or "Biology").strip()
        class_id = str(data.get("class_id") or data.get("classLevel") or "class_11").strip()
        chapter_id = str(data.get("chapter_id") or data.get("chapterId") or "").strip()
        chapter_name = str(data.get("chapter_name") or data.get("chapterName") or "General Biology").strip()
        duration = int(data.get("duration_minutes") or data.get("durationMinutes") or 30)
        total_marks = int(data.get("total_marks") or data.get("totalMarks") or 0)
        passing_marks = int(data.get("passing_marks") or data.get("passingMarks") or 0)
        negative_marking = bool(data.get("negative_marking") if "negative_marking" in data else data.get("negativeMarking", True))
        status = str(data.get("status") or "DRAFT").strip().upper()

        if not title:
            return {"success": False, "error": "Assessment title is required."}
        if asmt_type not in ASSESSMENT_TYPES:
            asmt_type = "CUSTOM_TEST"
        if status not in LIFECYCLE_STATES:
            status = "DRAFT"

        questions = data.get("questions") or data.get("questionSnapshots") or []
        question_ids = data.get("question_ids") or data.get("questionIds") or []
        if not question_ids and questions:
            question_ids = [str(q.get("id") or i) for i, q in enumerate(questions)]

        now_dt = datetime.datetime.now(timezone.utc)
        start_at = data.get("start_at") or data.get("startAt") or now_dt.isoformat()
        end_at = data.get("end_at") or data.get("endAt") or (now_dt + datetime.timedelta(minutes=duration)).isoformat()

        if not total_marks and questions:
            total_marks = len(questions) * 4
        if not passing_marks:
            passing_marks = max(1, int(total_marks * 0.4))

        asmt_id = f"asmt_{uuid.uuid4().hex[:12]}"
        now = _iso_now()

        asmt_doc = {
            "id": asmt_id,
            "assessmentId": asmt_id,
            "title": title,
            "type": asmt_type,
            "subject": subject,
            "class_id": class_id,
            "classLevel": class_id,
            "chapter_id": chapter_id,
            "chapterId": chapter_id,
            "chapter_name": chapter_name,
            "chapterName": chapter_name,
            "createdBy": creator_uid,
            "teacherName": creator_name,
            "status": status,
            "start_at": start_at,
            "startAt": start_at,
            "end_at": end_at,
            "endAt": end_at,
            "duration_minutes": duration,
            "durationMinutes": duration,
            "total_marks": total_marks,
            "totalMarks": total_marks,
            "passing_marks": passing_marks,
            "passingMarks": passing_marks,
            "negative_marking": negative_marking,
            "negativeMarking": negative_marking,
            "question_ids": question_ids,
            "questionIds": question_ids,
            "questions": questions,
            "questionSnapshots": questions,
            "createdAt": now,
            "updatedAt": now
        }

        firestore_store.save_doc("assessments", asmt_id, asmt_doc)
        return {"success": True, "assessment": asmt_doc}

    def get_assessment(self, assessment_id: str, role: str = "STUDENT", caller_uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        asmt = firestore_store.load_doc("assessments", assessment_id)
        if not asmt or not isinstance(asmt, dict):
            return None

        asmt = dict(asmt)
        dynamic_status = self.compute_dynamic_status(asmt)
        asmt["status"] = dynamic_status

        role_norm = str(role or "STUDENT").upper()

        if role_norm == "STUDENT" and dynamic_status == "DRAFT":
            return None

        # Synchronize question fields
        qs = asmt.get("questions") or asmt.get("questionSnapshots") or []

        # Strip answer keys for students unless test results are published
        if role_norm == "STUDENT" and dynamic_status != "RESULTS_AVAILABLE":
            sanitized = [_sanitize_question_for_student(q) for q in qs]
            asmt["questions"] = sanitized
            asmt["questionSnapshots"] = sanitized
        else:
            asmt["questions"] = qs
            asmt["questionSnapshots"] = qs

        return asmt

    def list_assessments(self, role: str = "STUDENT", caller_uid: Optional[str] = None,
                         status: Optional[str] = None, type_filter: Optional[str] = None,
                         chapter_id: Optional[str] = None, class_id: Optional[str] = None,
                         teacher_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        raw = firestore_store.list_docs("assessments")
        results = []
        role_norm = str(role or "STUDENT").upper()

        for doc in raw:
            if not isinstance(doc, dict):
                continue
            asmt = dict(doc)
            dynamic_status = self.compute_dynamic_status(asmt)
            asmt["status"] = dynamic_status

            if role_norm == "STUDENT":
                # Students never see DRAFT assessments
                if dynamic_status == "DRAFT":
                    continue

                qs = asmt.get("questions") or asmt.get("questionSnapshots") or []
                if dynamic_status != "RESULTS_AVAILABLE":
                    sanitized = [_sanitize_question_for_student(q) for q in qs]
                    asmt["questions"] = sanitized
                    asmt["questionSnapshots"] = sanitized
                else:
                    asmt["questions"] = qs
                    asmt["questionSnapshots"] = qs

            # Filters
            if status and asmt["status"].upper() != status.strip().upper():
                continue
            if type_filter and str(asmt.get("type", "")).upper() != type_filter.strip().upper():
                continue
            if chapter_id and str(asmt.get("chapter_id") or asmt.get("chapterId") or "") != chapter_id:
                continue
            if class_id and str(asmt.get("class_id") or asmt.get("classLevel") or "").lower() != class_id.lower():
                continue
            if teacher_id and str(asmt.get("createdBy", "")) != teacher_id:
                continue

            results.append(asmt)

        results.sort(key=lambda a: a.get("start_at") or a.get("startAt") or a.get("createdAt", ""), reverse=True)
        return results

    def get_upcoming_assessments(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        all_student_asmts = self.list_assessments(role="STUDENT")
        upcoming = []
        for a in all_student_asmts:
            st = a.get("status")
            if st in ("UPCOMING", "LIVE", "PUBLISHED"):
                if student_id:
                    sub = self.get_student_result(a.get("id"), student_id)
                    a["has_submitted"] = bool(sub)
                upcoming.append(a)

        upcoming.sort(key=lambda a: a.get("start_at") or a.get("startAt") or "")
        return upcoming

    def update_assessment(self, assessment_id: str, updates: Dict[str, Any], caller_uid: str = "", role: str = "TEACHER") -> Dict[str, Any]:
        asmt = firestore_store.load_doc("assessments", assessment_id)
        if not asmt:
            return {"success": False, "error": "Assessment not found."}

        is_admin = (str(role).upper() == "SUPER_ADMIN")
        if not is_admin and asmt.get("createdBy") != caller_uid:
            return {"success": False, "error": "Access denied: you can only edit assessments you created."}

        current_status = str(asmt.get("status", "DRAFT")).upper()
        if current_status not in ("DRAFT", "UPCOMING", "PUBLISHED"):
            return {"success": False, "error": f"Cannot modify assessment in state '{current_status}'."}

        allowed_fields = [
            "title", "type", "subject", "class_id", "classLevel", "chapter_id", "chapterId",
            "chapter_name", "chapterName", "start_at", "startAt", "end_at", "endAt",
            "duration_minutes", "durationMinutes", "total_marks", "totalMarks",
            "passing_marks", "passingMarks", "negative_marking", "negativeMarking",
            "question_ids", "questionIds", "questions", "questionSnapshots"
        ]
        for f in allowed_fields:
            if f in updates:
                asmt[f] = updates[f]

        if "questions" in updates:
            asmt["questionSnapshots"] = updates["questions"]
        elif "questionSnapshots" in updates:
            asmt["questions"] = updates["questionSnapshots"]

        asmt["updatedAt"] = _iso_now()
        firestore_store.save_doc("assessments", assessment_id, asmt)
        return {"success": True, "assessment": asmt}

    def transition_status(self, assessment_id: str, new_status: str, caller_uid: str = "", role: str = "TEACHER") -> Dict[str, Any]:
        new_status_norm = str(new_status or "").strip().upper()
        if new_status_norm not in LIFECYCLE_STATES:
            return {"success": False, "error": f"Invalid status. Must be one of: {', '.join(LIFECYCLE_STATES)}"}

        asmt = firestore_store.load_doc("assessments", assessment_id)
        if not asmt:
            return {"success": False, "error": "Assessment not found."}

        is_admin = (str(role).upper() == "SUPER_ADMIN")
        if not is_admin and asmt.get("createdBy") != caller_uid:
            return {"success": False, "error": "Access denied: you can only change status for assessments you created."}

        current_status = str(asmt.get("status", "DRAFT")).upper()
        if new_status_norm != current_status:
            allowed = ALLOWED_TRANSITIONS.get(current_status, set())
            if new_status_norm not in allowed and not is_admin:
                return {"success": False, "error": f"Invalid state transition: '{current_status}' -> '{new_status_norm}'."}

        asmt["status"] = new_status_norm
        asmt["updatedAt"] = _iso_now()
        firestore_store.save_doc("assessments", assessment_id, asmt)
        return {"success": True, "assessment": asmt, "new_status": new_status_norm}

    def submit_assessment(self, assessment_id: str, student_id: str, answers: Dict[Any, Any],
                          time_spent_seconds: int = 0, student_email: str = "", student_name: str = "") -> Dict[str, Any]:
        asmt = firestore_store.load_doc("assessments", assessment_id)
        if not asmt:
            return {"success": False, "error": "Assessment not found."}

        dynamic_status = self.compute_dynamic_status(asmt)
        now = datetime.datetime.now(timezone.utc)
        start_at = _parse_iso(asmt.get("start_at") or asmt.get("startAt"))
        end_at = _parse_iso(asmt.get("end_at") or asmt.get("endAt"))

        # Time Window Guards
        if start_at and now < start_at:
            return {"success": False, "error": "Test is not live yet. Early submissions are not permitted."}
        if end_at:
            grace_limit = end_at + datetime.timedelta(minutes=GRACE_PERIOD_MINUTES)
            if now > grace_limit and dynamic_status != "LIVE":
                return {"success": False, "error": "Assessment window has closed. Submissions are no longer accepted."}

        # Duplicate Prevention
        result_id = f"res_{assessment_id}_{student_id}"
        existing = firestore_store.load_doc("assessment_results", result_id)
        if existing:
            return {"success": False, "error": "You have already submitted this assessment. Duplicate submissions are not allowed."}

        questions = asmt.get("questions") or asmt.get("questionSnapshots") or []
        negative_marking = bool(asmt.get("negative_marking") if "negative_marking" in asmt else asmt.get("negativeMarking", True))

        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        question_responses = []
        concept_performance = {}

        for idx, q in enumerate(questions):
            # Check answer provided by key (idx or str(idx))
            chosen = answers.get(str(idx))
            if chosen is None:
                chosen = answers.get(idx)

            correct_ans = q.get("correct_index")
            if correct_ans is None:
                correct_ans = q.get("correct")
            if correct_ans is None:
                correct_ans = q.get("answer", 0)

            chapter = q.get("chapter") or asmt.get("chapter_name") or asmt.get("chapterName") or "General Biology"
            concept_id = q.get("concept_id") or q.get("concept") or chapter.lower().replace(" ", "_")

            if chosen is None or chosen == -1 or chosen == "":
                unattempted_count += 1
                outcome = "unattempted"
            elif int(chosen) == int(correct_ans):
                correct_count += 1
                outcome = "correct"
            else:
                incorrect_count += 1
                outcome = "incorrect"

            question_responses.append({
                "questionIndex": idx,
                "question_index": idx,
                "question": q.get("question") or q.get("q"),
                "chosen": chosen,
                "correct": correct_ans,
                "outcome": outcome,
                "chapter": chapter
            })

            if outcome != "unattempted":
                is_corr = (outcome == "correct")
                if concept_id not in concept_performance:
                    concept_performance[concept_id] = {"correct": 0, "total": 0, "chapter": chapter}
                concept_performance[concept_id]["total"] += 1
                if is_corr:
                    concept_performance[concept_id]["correct"] += 1

                # Feed into Adaptive BKT Learner Model
                try:
                    learner_manager.record_attempt(
                        student_id=student_id,
                        concept_id=concept_id,
                        chapter_id=q.get("chapter_id") or asmt.get("chapter_id") or asmt.get("chapterId") or "c01",
                        is_correct=is_corr,
                        difficulty=str(q.get("difficulty") or q.get("diff") or "medium").lower(),
                        topic_id=chapter
                    )
                except Exception:
                    pass

        total_qs = len(questions) or 1
        if negative_marking:
            score = (correct_count * 4) - (incorrect_count * 1)
        else:
            score = correct_count * 4

        percentage = round((correct_count / total_qs) * 100, 1)
        total_marks = asmt.get("total_marks") or asmt.get("totalMarks") or (total_qs * 4)

        result_doc = {
            "resultId": result_id,
            "id": result_id,
            "assessmentId": assessment_id,
            "assessment_id": assessment_id,
            "assessmentTitle": asmt.get("title"),
            "studentId": student_id,
            "student_id": student_id,
            "studentEmail": student_email,
            "studentName": student_name or student_id,
            "score": score,
            "totalMarks": total_marks,
            "total_marks": total_marks,
            "percentage": percentage,
            "correct": correct_count,
            "correct_count": correct_count,
            "incorrect": incorrect_count,
            "incorrect_count": incorrect_count,
            "unattempted": unattempted_count,
            "unattempted_count": unattempted_count,
            "totalQuestions": total_qs,
            "total_questions": total_qs,
            "timeSpentSeconds": time_spent_seconds,
            "time_spent_seconds": time_spent_seconds,
            "questionResponses": question_responses,
            "question_responses": question_responses,
            "conceptPerformance": concept_performance,
            "submittedAt": _iso_now()
        }

        firestore_store.save_doc("assessment_results", result_id, result_doc)
        return {
            "success": True,
            "result": result_doc,
            "score": score,
            "total_marks": total_marks,
            "percentage": percentage,
            "correct": correct_count,
            "correct_count": correct_count,
            "incorrect": incorrect_count,
            "incorrect_count": incorrect_count,
            "unattempted": unattempted_count,
            "unattempted_count": unattempted_count
        }

    def get_student_result(self, assessment_id: str, student_id: str) -> Optional[Dict[str, Any]]:
        result_id = f"res_{assessment_id}_{student_id}"
        res = firestore_store.load_doc("assessment_results", result_id)
        if not res:
            all_r = firestore_store.list_docs("assessment_results")
            for r in all_r:
                if isinstance(r, dict) and (r.get("assessmentId") == assessment_id or r.get("assessment_id") == assessment_id) and (r.get("studentId") == student_id or r.get("student_id") == student_id):
                    return r
        return res

    def get_assessment_results(self, assessment_id: str, caller_uid: str = "", role: str = "TEACHER") -> Dict[str, Any]:
        asmt = firestore_store.load_doc("assessments", assessment_id)
        if not asmt:
            return {"success": False, "error": "Assessment not found."}

        is_admin = (str(role).upper() == "SUPER_ADMIN")
        if not is_admin and asmt.get("createdBy") != caller_uid:
            return {"success": False, "error": "Access denied: you can only view results for assessments you created."}

        all_results = firestore_store.list_docs("assessment_results")
        matching = [r for r in all_results if isinstance(r, dict) and (r.get("assessmentId") == assessment_id or r.get("assessment_id") == assessment_id)]

        matching.sort(key=lambda r: (r.get("score", 0), -r.get("time_spent_seconds", r.get("timeSpentSeconds", 9999))), reverse=True)
        for rank, r in enumerate(matching, start=1):
            r["rank"] = rank

        scores = [r.get("score", 0) for r in matching]
        stats = {
            "total_submissions": len(matching),
            "totalAttempts": len(matching),
            "highest_score": max(scores) if scores else 0,
            "highestScore": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "lowestScore": min(scores) if scores else 0,
            "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "averageScore": round(sum(scores) / len(scores), 1) if scores else 0,
        }

        # Question-level performance analysis
        questions = asmt.get("questions") or asmt.get("questionSnapshots") or []
        question_analysis = []
        for i, q in enumerate(questions):
            corr_cnt = 0
            inc_cnt = 0
            un_cnt = 0
            for sub in matching:
                q_res = sub.get("question_responses") or sub.get("questionResponses") or []
                if i < len(q_res):
                    out = q_res[i].get("outcome")
                    if out == "correct":
                        corr_cnt += 1
                    elif out == "incorrect":
                        inc_cnt += 1
                    else:
                        un_cnt += 1
                else:
                    un_cnt += 1
            att = corr_cnt + inc_cnt
            acc = round((corr_cnt / att * 100), 1) if att > 0 else 0
            question_analysis.append({
                "question_index": i,
                "question": q.get("question") or q.get("q"),
                "correct_count": corr_cnt,
                "incorrect_count": inc_cnt,
                "unattempted_count": un_cnt,
                "accuracy": acc
            })

        return {
            "success": True,
            "assessment": asmt,
            "results": matching,
            "statistics": stats,
            "question_analysis": question_analysis
        }


assessment_engine = AssessmentEngine()
