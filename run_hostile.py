"""Hostile/adversarial evaluation: break the system, report honestly."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from adaptive_tutor import adaptive_tutor
from learner_model import learner_manager

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

# A. Rapid topic switching in one session
sid, h = "hos1", []
seq = [("explain mitochondria", "mitochondria"), ("now teach photosynthesis", "photosynthesis"),
       ("actually back to brain", "brain"), ("no wait glycolysis", "glycolysis")]
for q, needle in seq:
    r = ask(q, sid, h)
    h += [{"role": "user", "content": q}, {"role": "assistant", "content": str(r.get("reply", ""))[:300]}]
    check(f"switch: {q[:30]}", r.get("status") == "success" and needle in (str(r.get("title", "")) + str(r.get("reply", ""))).lower(), r.get("title"))

# B. Disguised non-biology (safe refusal OR grounded adjacent answer, never fabrication)
for q in ["explain the biology of a transistor", "what is the anatomy of a combustion engine",
          "describe the physiology of a stock market crash", "compare mitosis with photosynthesis rate in C++"]:
    r = ask(q, "hos2")
    check(f"disguised: {q[:40]}", r.get("mode") == "syllabus_restricted" or r.get("status") in ("success", "no_match"), f"{r.get('mode')}/{r.get('status')}")

# C. Invalid MCQ requests
for q in ["give me 0 questions", "give me hundred MCQs on cell", "quiz me on nothing", "mcq"]:
    try:
        r = ask(q, "hos3")
        check(f"mcq-edge: {q[:30]}", r.get("mode") in ("mcq_practice", "mcq_review", "syllabus_restricted", "local_adaptive") and r.get("status") in ("success", "mcq_reference", "out_of_syllabus", "no_match"), f"{r.get('mode')}/{r.get('status')}")
    except Exception as e:
        check(f"mcq-edge: {q[:30]}", False, f"EXC {e}")

# D. Follow-up after MCQ
sid = "hos4"
r1 = ask("Explain mitochondria.", sid)
r2 = ask("Give me 2 questions on it.", sid)
check("mcq-followup count", r2.get("mode") == "mcq_practice" and len(r2.get("mcqs", [])) == 2, f"{r2.get('mode')} n={len(r2.get('mcqs', []))}")

# E. Repeated-mistake full loop with strategy ladder (fresh student id per run)
import time as _t
sid = f"hos5_{int(_t.time())}"
r = ask("What is mitochondria?", sid)
cid, ch = r.get("concept_id"), r.get("chapter_id")
strats = []
for i in range(5):
    learner_manager.record_attempt(sid, cid, ch, False, topic_id="Mito")
    rr = ask("Explain mitochondria.", sid)
    strats.append(rr.get("strategy"))
check("escalation ladder", strats[0] in ("simplified_steps", "concrete_analogy") and "concrete_analogy" in strats and "remedial_diagnostic" in strats, strats)
# recovery
learner_manager.record_attempt(sid, cid, ch, True, topic_id="Mito")
learner_manager.record_attempt(sid, cid, ch, True, topic_id="Mito")
rr = ask("Explain mitochondria.", sid)
check("recovery de-escalates", rr.get("strategy") != "remedial_diagnostic", rr.get("strategy"))

# F. Malformed / empty / hostile inputs (must never crash, never answer garbage)
for q in ["", "???", "12345", "asdf qwerty", "please " * 200, "CELL??? mitochondria!!! glycolysis???"]:
    try:
        r = ask(q, "hos6")
        check(f"malformed ok: {q[:20]!r}", r.get("status") in ("success", "out_of_syllabus", "no_match", "mcq_reference"), r.get("status"))
    except Exception as e:
        check(f"malformed ok: {q[:20]!r}", False, f"EXC {e}")

# G. Case/whitespace torture on core concepts
for q, needle in [("  MiToChOnDrIa  ", "mitochondria"), ("GLYCOLYSIS", "glycolysis"),
                  ("   brain   ", "brain"), ("PhOtOsYnThEsIs", "photosynthesis")]:
    r = ask(q, "hos7")
    check(f"case: {q.strip()[:20]}", r.get("status") == "success" and needle in (str(r.get("title", "")) + str(r.get("reply", ""))).lower(), r.get("title"))

# H. Out-of-syllabus BIOLOGY (advanced/clinical): must refuse OR give a grounded
# adjacent answer with a scope note — never fabricate procedure/design details.
for q in ["explain CRISPR Cas9 guide RNA design rules in detail", "describe coronary artery bypass graft procedure steps"]:
    r = ask(q, "hos8")
    txt = str(r.get("reply", ""))
    has_note = "Scope note" in txt
    fabricates = ("cas9" in txt.lower().split("scope note")[0] and "design" in txt.lower() and "guide" in txt.lower() and "PAM" in txt) or ("bypass graft procedure" in txt.lower() and "sternotomy" in txt.lower())
    ok = r.get("mode") == "syllabus_restricted" or r.get("status") == "no_match" or (r.get("status") == "success" and has_note and not fabricates)
    check(f"oos-bio safe: {q[:35]}", ok, f"{r.get('mode')}/{r.get('status')} note={has_note} :: {str(r.get('title'))[:50]}")

print(f"\nHOSTILE: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
