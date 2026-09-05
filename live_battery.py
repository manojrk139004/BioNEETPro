import io, sys, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def post(path, payload, timeout=180):
    req = urllib.request.Request(
        "http://127.0.0.1:5000" + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())

tests = [
    ("compare xylem/phloem", {"query": "Compare xylem and phloem.", "student_id": "lv2", "history": [], "context": {}}),
    ("follow-up pronoun", {"query": "Why does it have folds?", "student_id": "lv2",
                           "history": [{"role": "user", "content": "Explain mitochondria."}], "context": {}}),
    ("non-bio reject", {"query": "What is Newtons second law?", "student_id": "lv3", "history": [], "context": {}}),
    ("mcq stays local", {"query": "Give me 2 MCQs on cockroach.", "student_id": "lv4", "history": [], "context": {}}),
]
for name, p in tests:
    b = post("/api/tutor/answer", p)
    r = b.get("reply", "")
    print(f"{name} | mode={b.get('mode')} status={b.get('status')} faith={b.get('faithfulness')} len={len(r)}")
    print("   title:", str(b.get("title"))[:70])
