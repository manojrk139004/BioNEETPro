"""Beast gate: golden tutor set -> pass rate, faithfulness, modes, citations, verdict."""
import json
import os
import time
from pathlib import Path

# Load server env (API key) so the gate measures the LIVE RAG path, not offline fallback.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env.local")
except ImportError:
    pass

from adaptive_tutor import adaptive_tutor

BASE = Path(__file__).resolve().parent
CASES = json.loads((BASE / "tests" / "golden_tutor.json").read_text(encoding="utf-8"))


def safe(s):
    return str(s).encode("ascii", "ignore").decode()


RESUME_FILE = BASE / "tests" / "gate_results.jsonl"

# Resume: skip questions already recorded (safe re-run after abort).
done = {}
if RESUME_FILE.exists():
    try:
        for line in RESUME_FILE.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            done[rec["q"]] = rec
    except Exception:
        pass

print(f"Loaded engine. Cases: {len(CASES)}, already done: {len(done)}", flush=True)
fout = open(RESUME_FILE, "a", encoding="utf-8")

for i, c in enumerate(CASES):
    if c["q"] in done:
        continue
    print(f"[{i+1}/{len(CASES)}] asking: {safe(c['q'][:60])} ...", flush=True)
    t0 = time.time()
    try:
        r = adaptive_tutor.generate_tutoring_response(query=c["q"], student_id="beast_eval")
        err = ""
    except Exception as exc:
        r = {}
        err = safe(str(exc)[:150])
    dt = time.time() - t0
    rec = {"q": c["q"], "expect": c["expect"], "must_contain": c.get("must_contain", []),
           "status": r.get("status", "CRASH"), "confidence": str(r.get("confidence", "")),
           "mode": r.get("mode", "?"), "faithfulness": r.get("faithfulness", 0) or 0,
           "reply": r.get("reply", ""), "error": err, "secs": round(dt, 1)}
    fout.write(json.dumps(rec) + "\n")
    fout.flush()
    print(f"  -> {rec['status']} {rec['confidence']} faith={rec['faithfulness']} {dt:.1f}s", flush=True)
    time.sleep(1.0)  # be kind to the free provider
fout.close()

# ---- verdict from the full results file ----
recs = []
for line in RESUME_FILE.read_text(encoding="utf-8").splitlines():
    try:
        recs.append(json.loads(line))
    except Exception:
        pass
# de-dupe by question (keep last)
latest = {}
for rec in recs:
    latest[rec["q"]] = rec

passed = failed = 0
faith = []
modes = {}
bio_total = bio_pass = 0
oos_total = oos_pass = 0
fail_list = []
for c in CASES:
    rec = latest.get(c["q"])
    if not rec:
        print(f"[PENDING] {safe(c['q'][:52])} (not run yet)")
        continue
    reply = rec.get("reply", "")
    status = rec.get("status", "")
    exp = c["expect"]
    modes[rec.get("mode", "?")] = modes.get(rec.get("mode", "?"), 0) + 1
    ok_status = (exp == "success" and status == "success") or \
        (exp == "out_of_syllabus" and status == "out_of_syllabus") or \
        (exp == "no_match_or_reject" and (status in ("no_match", "success") or rec.get("confidence") in ("LOW", "REJECTED")))
    ok_terms = all(t.lower() in reply.lower() for t in c.get("must_contain", []))
    has_cite = ("NCERT" in reply) if exp == "success" else True
    ok = ok_status and ok_terms and has_cite
    faith.append(rec.get("faithfulness", 0) or 0)
    if exp == "success":
        bio_total += 1
        bio_pass += 1 if ok else 0
    else:
        oos_total += 1
        oos_pass += 1 if ok else 0
    print(f"[{'PASS' if ok else 'FAIL'}] {safe(c['q'][:52])} status={status} conf={rec.get('confidence')} faith={rec.get('faithfulness')}")
    if not ok:
        print("   head:", safe(reply[:200].replace(chr(10), " ")))
        fail_list.append(c["q"])
    if ok:
        passed += 1
    else:
        failed += 1

avg_faith = sum(faith) / max(len(faith), 1)
print(f"\nBEAST: {passed}/{passed+failed} | bio {bio_pass}/{bio_total} | oos {oos_pass}/{oos_total} | faith {avg_faith:.3f} | modes {modes}")
bio_rate = bio_pass / max(bio_total, 1)
gate = bio_rate >= 0.95 and oos_pass == oos_total
print(f"GATE (bio>=95%% + oos=100%%):", "GREEN - SHIP IT" if gate else "RED - KEEP BUILDING")
if fail_list:
    print("FAILED QS:", len(fail_list))
