"""BioNEET-Pro — shared Firestore-first document store with local fallback.

One authoritative persistence implementation (per master-prompt constraint 2):
backend per-student documents live in Firestore collections; local JSON files
under data/ remain as an always-on cache/fallback so the app (and the guide
demo) works with or without backend credentials.

Setup (backend, one time):
  pip install firebase-admin
  Firebase console -> Project settings -> Service accounts -> Generate new
  private key -> save as serviceAccount.json in the project root (git-ignored),
  or set FIREBASE_SERVICE_ACCOUNT=/path/to/key.json,
  or FIREBASE_SERVICE_ACCOUNT_JSON='<inline json>'.
Without any of those, every function below silently uses local files only.
Secrets are never printed or logged here.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

_db = None
_init_attempted = False
_init_error = ""


def _init():
    global _db, _init_attempted, _init_error
    if _init_attempted:
        return _db
    _init_attempted = True
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        _init_error = "firebase-admin not installed"
        return None
    try:
        if not firebase_admin._apps:
            key_path = (
                os.environ.get("FIREBASE_SERVICE_ACCOUNT")
                or str(BASE_DIR / "serviceAccount.json")
            )
            inline = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
            if inline:
                cred = credentials.Certificate(json.loads(inline))
            elif key_path and Path(key_path).exists():
                cred = credentials.Certificate(key_path)
            else:
                _init_error = "no service account key found"
                return None
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    except Exception as e:
        _init_error = type(e).__name__
        _db = None
    return _db


def enabled() -> bool:
    """True when a live Firestore backend is reachable."""
    return _init() is not None


class FirestoreUnavailable(RuntimeError):
    """Raised when production-strict code requires Firestore but none is up."""


def require_firestore():
    """Fail explicitly when no live Firestore backend is reachable.

    Production (strict) write paths call this BEFORE touching local files so
    authoritative data is never silently stored on ephemeral container disk.
    Development keeps the local-JSON fallback (this function is simply not
    called there).
    """
    if not enabled():
        raise FirestoreUnavailable(
            "Firestore backend is required but unavailable: "
            + (_init_error or "unknown reason"))


def status() -> Dict[str, Any]:
    _init()
    return {"firestore_enabled": _db is not None,
            "reason": "" if _db is not None else _init_error}


def safe_id(student_id: str) -> str:
    return "".join(c for c in str(student_id or "")
                   if c.isalnum() or c in ("-", "_", "@", ".")) or "student_local"


def _local_path(collection: str, doc_id: str, subdir: Optional[str] = None) -> Path:
    d = DATA_DIR / (subdir or _collection_subdir(collection))
    d.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in str(doc_id) if c.isalnum() or c in ("-", "_")) or "doc"
    return d / f"{safe}.json"


def _collection_subdir(collection: str) -> str:
    return {
        "flashcards": "flashcard_state",
        "learner_profiles": "student_profiles",
        "dialogue_states": "dialogue_states",
        "score_predictions": "score_predictions",
        "tutor_states": "tutor_states",
        "chat_threads": "chat_threads",
        "teachers": "teachers",
        "assessments": "assessments",
        "assessment_results": "assessment_results",
        "assessmentResults": "assessment_results",
        "pending_mcqs": "pending_mcqs",
    }.get(collection, collection)


def load_doc(collection: str, doc_id: str, default: Any = None,
             subdir: Optional[str] = None) -> Any:
    """Cache-first read: local file first for ultra-low latency, with Firestore fallback."""
    path = _local_path(collection, doc_id, subdir)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    db = _init()
    if db is not None:
        try:
            snap = db.collection(collection).document(safe_id(doc_id)).get()
            if snap.exists:
                data = snap.to_dict()
                try:
                    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
                except Exception:
                    pass
                return data
        except Exception:
            pass
    return default


def save_doc(collection: str, doc_id: str, data: Any,
             subdir: Optional[str] = None) -> bool:
    """Write local cache synchronously (<1ms), then sync to Firestore asynchronously. Never blocks."""
    try:
        path = _local_path(collection, doc_id, subdir)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass
    db = _init()
    if db is not None:
        def _bg_sync():
            try:
                import copy
                payload = copy.deepcopy(data) if isinstance(data, dict) else {"value": data}
                db.collection(collection).document(safe_id(doc_id)).set(payload)
            except Exception:
                pass
        threading.Thread(target=_bg_sync, daemon=True).start()
        return True
    return False


def delete_doc(collection: str, doc_id: str, subdir: Optional[str] = None) -> None:
    try:
        p = _local_path(collection, doc_id, subdir)
        if p.exists():
            p.unlink()
    except Exception:
        pass
    db = _init()
    if db is not None:
        def _bg_del():
            try:
                db.collection(collection).document(safe_id(doc_id)).delete()
            except Exception:
                pass
        threading.Thread(target=_bg_del, daemon=True).start()


def list_docs(collection: str, subdir: Optional[str] = None) -> list:
    """Lists all documents in a collection. Reads local cache and merges with Firestore."""
    docs = {}
    db = _init()
    if db is not None:
        try:
            for snap in db.collection(collection).stream():
                d = snap.to_dict() or {}
                if "id" not in d:
                    d["id"] = snap.id
                docs[str(snap.id)] = d
        except Exception:
            pass

    # Merge local cache (local overrides/supplements Firestore with most recent writes)
    d = DATA_DIR / (subdir or _collection_subdir(collection))
    if d.exists():
        for p in d.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    doc_id = str(data.get("id") or data.get("uid") or data.get("resultId") or data.get("assessmentId") or p.stem)
                    data["id"] = doc_id
                    docs[doc_id] = data
            except Exception:
                pass
    return list(docs.values())

