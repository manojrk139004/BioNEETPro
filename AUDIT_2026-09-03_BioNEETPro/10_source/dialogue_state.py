"""
BioNEETPro - Persistent Dialogue State + FSRS-lite Review Scheduler (Phase 4)
Survives restarts (JSON per student). Tracks focal concept, turn count,
last strategy, and next-review dates per concept (1/3/7/14/30-day ladder
scaled by mastery — FSRS-lite without new deps).
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "data" / "dialogue_states"

INTERVALS = [1, 3, 7, 14, 30]


def _path(student_id: str) -> Path:
    safe = "".join(c for c in (student_id or "student_local") if c.isalnum() or c in ("-", "_")) or "student_local"
    return STATE_DIR / f"{safe}.json"


def load(student_id: str) -> Dict[str, Any]:
    p = _path(student_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"student_id": student_id, "turns": 0, "focal": None,
            "last_strategy": None, "reviews": {}, "updated_at": None}


def save(student_id: str, state: Dict[str, Any]):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    _path(student_id).write_text(json.dumps(state, indent=1), encoding="utf-8")


def record_turn(student_id: str, concept_id: Optional[str], title: Optional[str],
                strategy: Optional[str], mastery: Optional[float]):
    st = load(student_id)
    st["turns"] = int(st.get("turns", 0)) + 1
    if concept_id:
        st["focal"] = {"concept_id": concept_id, "title": title or concept_id}
    if strategy:
        st["last_strategy"] = strategy
    # FSRS-lite: higher mastery -> longer interval
    if concept_id and mastery is not None:
        try:
            m = float(mastery)
        except Exception:
            m = 0.5
        idx = 0 if m < 0.5 else (1 if m < 0.65 else (2 if m < 0.8 else (3 if m < 0.9 else 4)))
        nxt = datetime.now(timezone.utc) + timedelta(days=INTERVALS[idx])
        rev = st.setdefault("reviews", {})
        rev[concept_id] = {"next_review": nxt.isoformat(), "mastery": round(m, 3),
                           "title": title or concept_id}
    save(student_id, st)
    return st


def due_reviews(student_id: str) -> List[Dict[str, Any]]:
    st = load(student_id)
    now = datetime.now(timezone.utc)
    out = []
    for cid, r in (st.get("reviews") or {}).items():
        try:
            if datetime.fromisoformat(r["next_review"]) <= now:
                out.append({"concept_id": cid, **r})
        except Exception:
            continue
    return out
