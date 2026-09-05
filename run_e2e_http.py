"""End-to-end tests through the REAL HTTP path (exact frontend request flow)."""
import io, sys, json, time, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:5000"
PASS, FAIL = 0, 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name}")
    else:
        FAIL += 1
        print(f"FAIL {name} :: {detail}")

def post(path, payload, timeout=180):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(65)
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        raise

def chat(msg, sid, hist):
    """Mirrors frontend sendChat payload exactly."""
    return post("/chat", {"message": msg, "prefer_local": True, "history": hist[-8:],
                          "context": {"chapter": "", "topic": "", "goal": "NEET Biology 360/360"}})

# ---- PRIMARY DEMO FLOW (frontend-style, history accumulates) ----
sid, hist = "e2e_demo", []
def turn(q):
    global hist
    b = chat(q, sid, hist)
    r = b.get("reply", "")
    hist += [{"role": "user", "content": q}, {"role": "assistant", "content": r[:400]}]
    return b, r

b, r = turn("Explain mitochondria.")
check("demo-1 mitochondria", "mitochondria" in r.lower(), r[:80])
b, r = turn("Why does it have folds?")
check("demo-2 it=mitochondria", "mitochondria" in r.lower() or "cristae" in r.lower(), r[:80])
b, r = turn("What does that increase?")
check("demo-3 context", "mitochondria" in r.lower() or "cristae" in r.lower() or "surface" in r.lower(), r[:80])
b, r = turn("Give me 3 questions on it.")
nq = r.count("Question ")
check("demo-4 3 MCQs", nq >= 3, f"questions found: {nq}")
b, r = turn("I got question 2 wrong.")
check("demo-5 q2 reference", "question" in r.lower(), r[:100])
b1, r1 = turn("Explain it again.")
b2, r2 = turn("Explain it again.")
check("demo-6 adapted retry", len(r1) > 200 and ("analog" in r1.lower() or "mental model" in r1.lower() or "simple" in r1.lower() or "remediation" in r1.lower()), r1[:100])

# ---- MANDATORY CASES via /chat ----
MANDATORY = [
    ("teach me about cell", "cell"), ("teach me abt cell", "cell"),
    ("what is a cell", "cell"), ("explain mitochondria", "mitochondria"),
    ("why does mitochondria have folds?", "mitochondria"),
    ("teach me about brain", "brain"),
    ("explain glycolysis EMP pathway and ATP yield", "glycolysis"),
    ("teach me glycolysis from basics", "glycolysis"),
    ("why is ATP used in the first part of glycolysis?", "glycolysis"),
    ("give me 2 mcq on cockroach chapter", "cockroach"),
    ("give me 5 hard questions on genetics", "genetics"),
    ("teach me about xylem", "xylem"), ("teach me about phloem", "phloem"),
    ("what is the difference between xylem and phloem", "xylem"),
    ("compare xylem and phloem", "xylem"), ("xylem vs phloem", "xylem"),
    ("how are xylem and phloem different", "xylem"),
    ("explain glycolysis and Krebs cycle", "glycolysis"),
    ("compare mitochondria and chloroplast", "mitochondria"),
    ("what is Newton's second law?", None),
]
for i, (q, needle) in enumerate(MANDATORY):
    b = chat(q, f"e2e_m{i}", [])
    r = b.get("reply", "")
    if needle is None:
        check(f"e2e reject: {q[:35]}", "specialized" in r or "Syllabus Boundary" in r, r[:80])
    elif "mcq" in q or "questions on genetics" in q:
        check(f"e2e mcq: {q[:35]}", r.count("Question ") >= 2, f"n={r.count('Question ')}")
    elif "difference" in q or "compare" in q or q.startswith("xylem vs") or "different" in q or ("glycolysis and Krebs" in q) or ("mitochondria and chloroplast" in q):
        check(f"e2e multi: {q[:35]}", needle in r.lower() and ("Compare at a glance" in r or "Krebs" in r or "chloroplast" in r.lower()), r[:80])
    else:
        check(f"e2e: {q[:35]}", needle in r.lower(), r[:80])

# ---- /api/tutor/answer observability fields ----
b = post("/api/tutor/answer", {"query": "Explain mitochondria.", "student_id": "e2e_obs", "history": [], "context": {}})
need = ["reply", "mode", "status", "confidence", "concept_id", "chapter_id", "strategy", "hybrid_score", "resolved_query", "citations", "latency_ms"]
check("observability fields", all(k in b for k in need), [k for k in need if k not in b])
c0 = (b.get("citations") or [{}])[0]
check("traceability", all(k in c0 for k in ("title", "source", "section", "page_number", "chunk_id")), c0)

# ---- learner update via HTTP ----
b = post("/api/mcq/submit", {"student_id": "e2e_learn", "concept_id": "BIO-C08-01", "chapter_id": "c08", "is_correct": False, "topic_id": "Mito"})
check("learner update http", "new_mastery" in b and b["new_mastery"] < b["prior_mastery"], b)
b = post("/api/tutor/answer", {"query": "Explain it again.", "student_id": "e2e_learn", "history": [{"role": "user", "content": "Explain mitochondria."}], "context": {}})
check("weak learner adapts via http", b.get("strategy") in ("concrete_analogy", "simplified_steps", "remedial_diagnostic", "process_flow"), b.get("strategy"))

print(f"\nE2E-HTTP: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
