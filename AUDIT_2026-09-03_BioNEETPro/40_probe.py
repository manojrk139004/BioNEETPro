"""FORENSIC PROBE (audit-only). Calls production code paths, records behavior.
Writes 41_runtime_results.jsonl. Uses student_id 'forensic_probe' (cleaned after)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

from adaptive_tutor import adaptive_tutor
from mcq_engine import mcq_engine
from nlp_pipeline import nlp_pipeline
from learner_model import learner_manager

SID = "forensic_probe"
OUT = Path(__file__).resolve().parent / "41_runtime_results.jsonl"

CHAT = [
    "teach me about cell",
    "teach me abt cell",
    "what is a cell",
    "explain mitochondria",
    "why does mitochondria have folds?",
    "what does that increase?",
    "teach me about brain",
    "explain glycolysis EMP pathway and ATP yield",
    "teach me glycolysis from basics",
    "why is ATP used in the first part of glycolysis?",
    "what happens after glucose becomes pyruvate?",
    "why?",
    "explain it again",
    "what is Newton's second law?",
    "mitocondria powrhouse of cell",
    "diff b/w mitosis meiosis",
    "Krebs?",
    "compare xylem vs phloem tissue including what each transports and where they are found in the plant body",
    "function of ribosomes",
    " explain   ATP!!! ",
    "",
    "asdkfjh qwerty zzz",
    "what is molarity?",
    "stock market tips",
    "now teach me heart",
]
MCQ_QS = [
    "give me 2 mcq on cockroach",
    "give me five hard questions on genetics",
    "give me questions from my weak topics",
    "give me 3 questions on this",
]


def chat_case(q, history):
    nlp = nlp_pipeline.process_query(q, history, student_id=SID)
    t0 = time.time()
    try:
        r = adaptive_tutor.generate_tutoring_response(query=q, student_id=SID, history=history)
        err = ""
    except Exception as exc:
        r, err = {}, f"CRASH: {exc}"[:200]
    return {
        "input": q,
        "normalized": nlp.get("normalized_query", ""),
        "resolved": nlp.get("resolved_query", ""),
        "intent": nlp.get("intent", ""),
        "concept": nlp.get("canonical_concept"),
        "syllabus_valid": nlp.get("syllabus_valid"),
        "mode": r.get("mode", "CRASH"),
        "status": r.get("status", "CRASH"),
        "confidence": str(r.get("confidence", "")),
        "title": (r.get("title", "") or "")[:80],
        "chapter": r.get("chapter_id", ""),
        "score": r.get("hybrid_score"),
        "strategy": r.get("strategy", ""),
        "citations": len(r.get("citations", []) or []),
        "has_check_mcq": bool(r.get("check_mcq")),
        "faithfulness": r.get("faithfulness"),
        "reply_head": (r.get("reply", "") or "")[:300].replace("\n", " "),
        "secs": round(time.time() - t0, 1),
        "error": err,
    }


def done_inputs():
    if not OUT.exists():
        return {}
    seen = {}
    try:
        for line in OUT.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                seen[rec.get("input")] = True
            except Exception:
                pass
    except Exception:
        pass
    return seen


def save(rec):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


def main():
    seen = done_inputs()
    print(f"resuming, {len(seen)} already recorded", flush=True)
    history = []
    # Part 7 chained conversation (history accumulates like the real client)
    chain = ["Explain mitochondria.", "Why does it have folds?", "What does that increase?",
             "Give me 3 questions on it.", "I got question 2 wrong.", "Explain it again."]
    for q in chain:
        if q in seen:
            # rebuild history shape without re-calling (order preserved by chain list)
            history.append({"role": "user", "content": q})
            history.append({"role": "assistant", "content": "[recorded]"})
            continue
        print(f"chain: {q}", flush=True)
        rec = chat_case(q, history)
        rec["chain"] = True
        save(rec)
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": rec["reply_head"][:500]})
    for q in CHAT:
        if q in seen:
            continue
        print(f"chat: {q[:60]}", flush=True)
        save(chat_case(q, []))
    for q in MCQ_QS:
        if q in seen:
            continue
        print(f"mcq: {q[:60]}", flush=True)
        try:
            m = mcq_engine.generate_mcqs(q, student_id=SID)
            save({"input": q, "intent": "mcq_request", "mode": "mcq_generate",
                  "count": m.get("count"), "difficulty": m.get("difficulty"),
                  "difficulty_mode": m.get("difficulty_mode"), "topic": m.get("topic"),
                  "first_q": ((m.get("mcqs") or [{}])[0].get("question", "") or "")[:120]})
        except Exception as exc:
            save({"input": q, "mode": "CRASH", "error": str(exc)[:200]})
    # learner separation check: different user, same question
    if "[separation] explain mitochondria as user B" not in seen:
        print("separation check", flush=True)
        r2 = adaptive_tutor.generate_tutoring_response(query="explain mitochondria", student_id="forensic_probe_B")
        save({"input": "[separation] explain mitochondria as user B", "mode": r2.get("mode"),
              "mastery": r2.get("concept_mastery")})
    print("probe complete", flush=True)


if __name__ == "__main__":
    main()
