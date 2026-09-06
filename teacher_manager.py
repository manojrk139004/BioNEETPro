"""
BioNEETPro V2 — Teacher Management Service
Manages teacher provisioning, role assignment, status toggling, and metadata.
"""

import datetime
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Union
import firestore_store

VALID_STATUSES = {"ACTIVE", "INACTIVE", "active", "inactive"}


def _validate_email(email: str) -> bool:
    if not email or "@" not in email or "." not in email:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))


class TeacherManager:
    def __init__(self):
        pass

    def is_super_admin(self, uid: Optional[str] = None, claims: Optional[Dict[str, Any]] = None) -> bool:
        claims = claims or {}
        return claims.get("admin") is True or str(claims.get("role") or "").upper() in ("SUPER_ADMIN", "ADMIN")

    def is_teacher(self, teacher_uid: Optional[str] = None) -> bool:
        if not teacher_uid:
            return False
        t = self.get_teacher(str(teacher_uid))
        if t and str(t.get("status", "ACTIVE")).upper() != "INACTIVE":
            return True
        return False

    def create_teacher(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Creates a teacher record. Supports both:
        create_teacher(data, creator_uid=...)
        create_teacher(admin_uid, data)
        """
        if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            admin_uid = args[0]
            data = args[1]
        elif len(args) >= 1 and isinstance(args[0], dict):
            data = args[0]
            admin_uid = kwargs.get("creator_uid") or kwargs.get("admin_uid") or "admin"
        else:
            data = kwargs.get("data") or {}
            admin_uid = kwargs.get("creator_uid") or kwargs.get("admin_uid") or "admin"

        name = str(data.get("name") or "").strip()
        email = str(data.get("email") or "").strip().lower()
        department = str(data.get("department") or "Biology").strip()
        subjects = data.get("subjects") or ["Biology"]
        phone = str(data.get("phone") or "").strip()
        password = str(data.get("password") or "").strip()

        if not name or len(name) < 2:
            return {"success": False, "error": "Teacher name must be at least 2 characters."}
        if not _validate_email(email):
            return {"success": False, "error": "Invalid email address provided."}

        # Check for existing teacher email
        existing_teachers = self.list_teachers()
        for t in existing_teachers:
            if t.get("email", "").lower() == email:
                return {"success": False, "error": f"Teacher with email '{email}' already exists."}

        # Provision UID
        teacher_uid = str(data.get("uid") or "").strip()
        if not teacher_uid:
            try:
                import firebase_admin.auth as fb_auth
                if password and len(password) >= 6:
                    user_record = fb_auth.create_user(
                        email=email,
                        password=password,
                        display_name=name
                    )
                    teacher_uid = user_record.uid
                    fb_auth.set_custom_user_claims(teacher_uid, {"role": "teacher", "teacher": True})
            except Exception:
                pass

            if not teacher_uid:
                teacher_uid = f"teacher_{uuid.uuid4().hex[:12]}"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        teacher_doc = {
            "uid": teacher_uid,
            "id": teacher_uid,
            "name": name,
            "email": email,
            "role": "TEACHER",
            "department": department,
            "subjects": subjects if isinstance(subjects, list) else [subjects],
            "phone": phone,
            "status": "ACTIVE",
            "createdAt": now,
            "updatedAt": now,
            "createdBy": admin_uid
        }

        firestore_store.save_doc("teachers", teacher_uid, teacher_doc)
        firestore_store.save_doc("users", teacher_uid, teacher_doc)

        return {"success": True, "teacher": teacher_doc}

    def list_teachers(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        teachers = firestore_store.list_docs("teachers")
        users = firestore_store.list_docs("users")
        t_map = {}
        for t in teachers:
            if isinstance(t, dict):
                uid = str(t.get("uid") or t.get("id"))
                t_map[uid] = t
        for u in users:
            if isinstance(u, dict) and str(u.get("role", "")).upper() == "TEACHER":
                uid = str(u.get("uid") or u.get("id"))
                if uid not in t_map:
                    t_map[uid] = u

        res = list(t_map.values())
        if status:
            s_up = status.strip().upper()
            res = [t for t in res if str(t.get("status", "")).upper() == s_up]

        return res

    def get_teacher(self, teacher_uid: str) -> Optional[Dict[str, Any]]:
        t = firestore_store.load_doc("teachers", teacher_uid)
        if not t:
            t = firestore_store.load_doc("users", teacher_uid)
        if t and (str(t.get("role", "")).upper() == "TEACHER" or "teacher" in str(t.get("uid", ""))):
            return t
        return None

    def update_status(self, teacher_uid: str, status: str, admin_uid: str = "admin") -> Dict[str, Any]:
        status_norm = str(status or "").strip().upper()
        if status_norm not in ("ACTIVE", "INACTIVE"):
            return {"success": False, "error": "Status must be either 'ACTIVE' or 'INACTIVE'."}

        teacher = self.get_teacher(teacher_uid)
        if not teacher:
            return {"success": False, "error": "Teacher not found."}

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        teacher["status"] = status_norm
        teacher["updatedAt"] = now
        teacher["updatedBy"] = admin_uid

        firestore_store.save_doc("teachers", teacher_uid, teacher)
        firestore_store.save_doc("users", teacher_uid, teacher)

        try:
            import firebase_admin.auth as fb_auth
            fb_auth.update_user(teacher_uid, disabled=(status_norm == "INACTIVE"))
        except Exception:
            pass

        return {"success": True, "teacher": teacher, "new_status": status_norm}

    def edit_teacher(self, teacher_uid: str, updates: Dict[str, Any], admin_uid: str = "admin") -> Dict[str, Any]:
        teacher = self.get_teacher(teacher_uid)
        if not teacher:
            return {"success": False, "error": "Teacher not found."}

        if "name" in updates:
            name = str(updates["name"] or "").strip()
            if len(name) >= 2:
                teacher["name"] = name
        if "department" in updates:
            teacher["department"] = str(updates["department"] or "").strip()
        if "subjects" in updates:
            subjs = updates["subjects"]
            teacher["subjects"] = subjs if isinstance(subjs, list) else [subjs]
        if "phone" in updates:
            teacher["phone"] = str(updates["phone"] or "").strip()

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        teacher["updatedAt"] = now
        teacher["updatedBy"] = admin_uid

        firestore_store.save_doc("teachers", teacher_uid, teacher)
        firestore_store.save_doc("users", teacher_uid, teacher)

        return {"success": True, "teacher": teacher}


teacher_manager = TeacherManager()
