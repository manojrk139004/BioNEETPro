"""Unseen + adversarial verification for BioNEETPro hardening fixes."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from adaptive_tutor import adaptive_tutor
from nlp_pipeline import nlp_pipeline
from mcq_engine import mcq_engine

PASS, FAIL = 0, 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name}")
    else:
        FAIL += 1
        print(f"FAIL {name} :: {detail}")

def ask(q, sid, hist=None):
    return adaptive_tutor.generate_tutoring_response(q, student_id=sid, history=hist or [])

# 1. Mandatory cases
r = ask("teach me about cell", "m1")
check("cell broad overview", "WHAT IS A CELL" in str(r.get("title", "")).upper() or "OVERVIEW OF CELL" in str(r.get("title", "")).upper(), r.get("title"))
r = ask("teach me abt cell", "m2")
check("shorthand abt cell", r.get("status") == "success" and "Cell" in str(r.get("title", "")), r.get("title"))
r = ask("explain mitochondria", "m3")
check("mitochondria", "mitochondria" in str(r.get("title", "")).lower(), r.get("title"))
r = ask("why does mitochondria have folds?", "m4")
check("cristae folds", "mitochondria" in str(r.get("title", "")).lower(), r.get("title"))
r = ask("teach me about brain", "m5")
check("brain broad overview", "CENTRAL NEURAL" in str(r.get("title", "")).upper(), r.get("title"))
r = ask("explain glycolysis EMP pathway and ATP yield", "m6")
check("glycolysis EMP", "GLYCOLYSIS" in str(r.get("title", "")).upper(), r.get("title"))
r = ask("teach me glycolysis from basics", "m7")
check("glycolysis basics strategy", r.get("strategy") == "simplified_steps", r.get("strategy"))
r = ask("why is ATP used in the first part of glycolysis?", "m8")
check("atp glycolysis", "GLYCOLYSIS" in str(r.get("title", "")).upper(), r.get("title"))
r = ask("what happens after glucose becomes pyruvate?", "m9")
check("pyruvate follow", r.get("status") == "success", r.get("title"))
r = ask("give me 2 mcq on cockroach chapter", "m10")
check("mcq cockroach routed", r.get("mode") == "mcq_practice" and len(r.get("mcqs", [])) == 2, f"{r.get('mode')} n={len(r.get('mcqs', []))}")
r = ask("give me 5 hard questions on genetics", "m11")
check("mcq genetics hard", r.get("mode") == "mcq_practice" and len(r.get("mcqs", [])) == 5 and r.get("mcq_difficulty") == "hard",
      f"{r.get('mode')} n={len(r.get('mcqs', []))} d={r.get('mcq_difficulty')}")
r = ask("what is Newton's second law?", "m12")
check("newton rejected", r.get("mode") == "syllabus_restricted", r.get("mode"))

# 2. Intent distinctions
n = nlp_pipeline.process_query("I got question 2 wrong", [], student_id="i1")
check("answer-report intent", n["intent"] in ("quiz_feedback", "mcq_answer"), n["intent"])
n = nlp_pipeline.process_query("what is question 2", [], student_id="i1")
check("qref intent", n["intent"] == "mcq_reference", n["intent"])
n = nlp_pipeline.process_query("give me 2 questions on respiration", [], student_id="i1")
check("request-2 intent", n["intent"] == "mcq_request", n["intent"])

# 3. Quantity words
check("qty five", mcq_engine.parse_mcq_request("give me five questions on heart", student_id="q1")["requested_count"] == 5, "")
check("qty three detached", mcq_engine.parse_mcq_request("quiz me with three on respiration", student_id="q1")["requested_count"] == 3, "")
check("qty two", mcq_engine.parse_mcq_request("give me two MCQs", student_id="q1")["requested_count"] == 2, "")
check("qty ten", mcq_engine.parse_mcq_request("ask 10 questions", student_id="q1")["requested_count"] == 10, "")

# 4. Unseen paraphrases / typos / shorthand
for q, needle in [
    ("tll me abt powerhouse of cell", "mitochondria"),
    ("explain mitocondria", "mitochondria"),    ("basic unit of life kya hai", "cell"),
    ("EMP pathway kya hota hai", "glycolysis"),
    ("glycolytic pathway and atp formation", "glycolysis"),
    ("folds of mitochondria ka function", "mitochondria"),
    ("tell me about earthworm", "annelida"),
    ("explain SA node function", "cardiac"),
    ("what are IUDs", "iud"),
    ("COMPARE XYLEM AND PHLOEM", "xylem"),
    ("diff b/w mitosis and meiosis", "meiosis"),
    ("aerobic vs anaerobic respiration", "respir"),
]:
    r = ask(q, "u_" + needle[:4])
    ok = r.get("status") == "success" and needle in (str(r.get("title", "")) + str(r.get("reply", ""))[:500]).lower()
    check(f"unseen: {q[:40]}", ok, r.get("title"))

# 5. Non-biology / out-of-syllabus rejections
for q in ["derive the quadratic formula", "write python code for sorting", "who won the cricket match",
          "explain thermodynamics enthalpy", "what is Kirchhoff's law"]:
    r = ask(q, "n1")
    check(f"reject: {q[:35]}", r.get("mode") == "syllabus_restricted", r.get("mode"))

# 6. Weak-topic + difficulty override
from learner_model import learner_manager
sid = "w1"
prof = learner_manager.get_or_create_profile(sid)
for _ in range(2):
    learner_manager.record_attempt(sid, "BIO-C14-01", "c14", False, topic_id="Glycolysis")
d = mcq_engine.generate_mcqs("give me questions from my weak topics", student_id=sid)
check("weak topics mode", d["status"] == "success" and d["count"] >= 1, d.get("topic"))
d2 = mcq_engine.generate_mcqs("give me 3 easy questions on heart", student_id=sid)
check("explicit easy overrides", d2["difficulty"] == "easy", d2["difficulty"])

# 7. MCQ validity sweep
d3 = mcq_engine.generate_mcqs("give me 10 questions on cell", student_id="v2")
allok = all(mcq_engine.validate_mcq(m) for m in d3["mcqs"]) and len(d3["mcqs"]) == 10
check("10 MCQs all valid", allok, f"n={len(d3['mcqs'])}")

# 8b. Comparison returns both sides + contrast table
from retrieval_engine import retrieval_engine as _re
_cmp = _re.search("difference between mitosis and meiosis", top_k=4)
sides = {c.get("compare_side") for c in _cmp}
check("comparison both sides", sides == {"A", "B"} and _cmp[0].get("is_comparison"), f"{sides}")
r = ask("difference between mitosis and meiosis", "cmp1")
check("comparison table rendered", "Compare at a glance" in str(r.get("reply", "")), r.get("title"))
sid = "sw1"
r1 = ask("explain mitochondria", sid)
r2 = ask("now teach me photosynthesis", sid)
r3 = ask("back to mitochondria, why folds?", sid)
check("topic switch", "photosynthesis" in str(r2.get("title", "")).lower(), r2.get("title"))
check("topic return", "mitochondria" in str(r3.get("title", "")).lower(), r3.get("title"))

print(f"\n==== {PASS} passed, {FAIL} failed ====")
sys.exit(1 if FAIL else 0)
