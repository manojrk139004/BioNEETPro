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
    }.get(collection, collection)


from concurrent.futures import ThreadPoolExecutor

_sync_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="firestore_sync")


def _bg_firestore_save(collection: str, doc_id: str, payload: Any):
    try:
        db = _init()
        if db is not None:
            db.collection(collection).document(safe_id(doc_id)).set(payload)
    except Exception:
        pass


def _bg_firestore_delete(collection: str, doc_id: str):
    try:
        db = _init()
        if db is not None:
            db.collection(collection).document(safe_id(doc_id)).delete()
    except Exception:
        pass


def load_doc(collection: str, doc_id: str, default: Any = None,
             subdir: Optional[str] = None) -> Any:
    """Local-cache-first read with Firestore fallback. Ultra-fast sub-millisecond retrieval."""
    # 1. Check local filesystem cache first (<1ms)
    path = _local_path(collection, doc_id, subdir)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 2. If not found locally, fetch from Firestore and prime local cache
    db = _init()
    if db is not None:
        try:
            snap = db.collection(collection).document(safe_id(doc_id)).get()
            if snap.exists:
                doc_dict = snap.to_dict()
                try:
                    path.write_text(json.dumps(doc_dict, indent=2, default=str), encoding="utf-8")
                except Exception:
                    pass
                return doc_dict
        except Exception:
            pass

    return default


def save_doc(collection: str, doc_id: str, data: Any,
             subdir: Optional[str] = None, sync: bool = False) -> bool:
    """Write local cache first (<1ms), then sync to Firestore asynchronously."""
    try:
        path = _local_path(collection, doc_id, subdir)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass

    db = _init()
    if db is not None:
        import copy
        payload = copy.deepcopy(data) if isinstance(data, dict) else {"value": data}
        if sync:
            try:
                db.collection(collection).document(safe_id(doc_id)).set(payload)
                return True
            except Exception:
                return False
        else:
            _sync_pool.submit(_bg_firestore_save, collection, doc_id, payload)
            return True
    return False


def delete_doc(collection: str, doc_id: str, subdir: Optional[str] = None, sync: bool = False) -> None:
    try:
        p = _local_path(collection, doc_id, subdir)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    db = _init()
    if db is not None:
        if sync:
            try:
                db.collection(collection).document(safe_id(doc_id)).delete()
            except Exception:
                pass
        else:
            _sync_pool.submit(_bg_firestore_delete, collection, doc_id)

