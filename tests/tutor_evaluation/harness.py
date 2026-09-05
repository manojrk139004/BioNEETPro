"""Shared harness for tutor evaluation suites (deterministic local pipeline).

Uses the REAL shipped stack: app.build_unified_answer -> adaptive_tutor ->
nlp + retrieval + local generation. No tutor-internal mocks. Each conversation
gets a fresh student id so tracker state never leaks between cases.
"""
import os
import sys
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DEV_AUTH_MODE", "true")
# Evaluation speed: use the documented local-JSON persistence fallback instead
# of live Firestore roundtrips (~2.8s vs ~11s per turn). Tutor logic (NLP,
# retrieval, generation, tracking) is identical; Firestore-ON parity is
# verified separately on a sampled subset (see evaluation report).
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT",
                      r"C:\nonexistent\tutor-eval-local.json")

from app import build_unified_answer  # noqa: E402


def new_sid(prefix="tuteval"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def ask(query, sid, history, context=None):
    """One turn through the real pipeline. Returns (output, new_history)."""
    out = build_unified_answer(query, sid, history, context or {},
                               include_steps=False)
    history = list(history) + [{"role": "user", "content": query},
                               {"role": "assistant",
                                "content": (out.get("reply") or "")[:800]}]
    return out, history


def blob(out):
    """All user-visible topic evidence in one lowercase string."""
    parts = [out.get("title") or "", out.get("reply") or "",
             (out.get("chapter_id") or "")]
    try:
        from syllabus import syllabus_validator  # noqa
        for cls in ("class_11", "class_12"):
            for unit, ud in (syllabus_validator.syllabus.get(cls) or {}).items():
                ch = (ud.get("chapters") or {}).get(
                    str(out.get("chapter_id") or "").lower())
                if ch and ch.get("chapter_name"):
                    parts.append(ch["chapter_name"])
    except Exception:
        pass
    for c in out.get("citations") or []:
        parts.append(str(c.get("section") or "") + " " +
                     str(c.get("chapter") or ""))
    return "\n".join(parts).lower()


def topic_hit(out, tokens):
    b = blob(out)
    return any(t.lower() in b for t in tokens)


def chapter_hit(out, hint):
    if not hint:
        return None
    return hint.lower() in blob(out)


def run_conversation(prompts, sid=None, context=None):
    """Run a multi-turn conversation. Returns (sid, [(prompt, out)])."""
    sid = sid or new_sid()
    history = []
    turns = []
    for p in prompts:
        out, history = ask(p, sid, history, context)
        turns.append((p, out))
    return sid, turns
