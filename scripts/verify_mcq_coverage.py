#!/usr/bin/env python3
"""Independent MCQ coverage + quality verifier for BioNEETPro.

Checks BOTH data/indexed_mcqs_cache.json (engine pool) and
data/mcq_firestore_seed.json (admin Firestore sync) for:
  - per-chapter counts vs 200 target (33 chapters)
  - structural validity (question, 4 distinct options, correct index,
    answer-in-options, explanation, chapter)
  - exact + near-duplicate questions
  - placeholder / garbage detection

Usage: python scripts/verify_mcq_coverage.py
Exit code 0 only if 33/33 chapters >= 200 valid in BOTH files.
Writes MCQ_COVERAGE_REPORT.json.
"""
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "data" / "indexed_mcqs_cache.json"
SEED = BASE / "data" / "mcq_firestore_seed.json"
OUT = BASE / "MCQ_COVERAGE_REPORT.json"
TARGET = 200

PLACEHOLDER = re.compile(r"lorem|placeholder|todo|xxx+|test question\s*\d*$", re.I)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"LOAD FAIL {path.name}: {e}")
        return None


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def validate(m):
    """Returns (ok, reason). Accepts both cache + seed schemas."""
    q = str(m.get("question") or "").strip()
    if len(q) <= 10:
        return False, "short/missing question"
    opts = m.get("options")
    if not isinstance(opts, list) or len(opts) != 4:
        return False, "options != 4"
    if any(not str(o).strip() for o in opts):
        return False, "empty option"
    # Distinctness is case-SENSITIVE (matches backend LocalMCQEngine.validate_mcq):
    # e.g. "Mangifera Indica Linn." vs "Mangifera indica Linn." are intentionally
    # distinct options in a binomial-nomenclature question.
    if len({str(o).strip() for o in opts}) != 4:
        return False, "duplicate options"
    ci = m.get("correct_index", m.get("correct", None))
    try:
        ci = int(ci)
    except Exception:
        return False, "bad correct index"
    if not (0 <= ci < 4):
        return False, "correct index out of range"
    ans = str(m.get("correct_answer", opts[ci])).strip()
    if norm(ans) != norm(opts[ci]):
        return False, "answer not in options"
    if not str(m.get("explanation") or "").strip():
        return False, "missing explanation"
    if not str(m.get("chapter") or "").strip():
        return False, "missing chapter"
    if PLACEHOLDER.search(q):
        return False, "placeholder/garbage"
    return True, ""


def audit(items):
    per_chapter = Counter()
    per_valid = Counter()
    invalid = []
    seen_exact = {}
    dup_exact = 0
    for i, m in enumerate(items):
        ch = str(m.get("chapter") or "?").strip()
        per_chapter[ch] += 1
        ok, reason = validate(m)
        if ok:
            per_valid[ch] += 1
        else:
            invalid.append({"index": i, "chapter": ch,
                            "question": str(m.get("question") or "")[:80],
                            "reason": reason})
        nq = norm(m.get("question") or "")
        if nq and len(nq) > 15:
            if nq in seen_exact:
                dup_exact += 1
            else:
                seen_exact[nq] = i
    # near-dup sample: pairwise on first 2000 is O(n^2); use token-prefilter
    near_dup = 0
    qs = [norm(m.get("question") or "") for m in items]
    buckets = {}
    for q in qs:
        if len(q) < 20:
            continue
        buckets.setdefault(" ".join(sorted(set(q.split()))[:0]) or q[:12], []).append(q)
    checked = 0
    for key, bq in buckets.items():
        for a in range(len(bq)):
            for c in range(a + 1, min(a + 6, len(bq))):
                checked += 1
                if checked > 20000:
                    break
                if difflib.SequenceMatcher(None, bq[a], bq[c]).ratio() >= 0.92:
                    near_dup += 1
            if checked > 20000:
                break
    return per_chapter, per_valid, invalid, dup_exact, near_dup


def main():
    report = {"target_per_chapter": TARGET, "files": {}}
    overall_ok = True
    for path in (CACHE, SEED):
        items = load(path)
        if items is None:
            report["files"][path.name] = {"error": "unreadable"}
            overall_ok = False
            continue
        pc, pv, invalid, dexact, near = audit(items)
        chapters = sorted(set(list(pc.keys())))
        rows = []
        for ch in chapters:
            tot = pc[ch]
            val = pv[ch]
            rows.append({"chapter": ch, "current_count": tot,
                         "valid_count": val, "target": TARGET,
                         "missing": max(0, TARGET - val),
                         "final_count": val,
                         "status": "PASS" if val >= TARGET else "FAIL"})
        n_pass = sum(1 for r in rows if r["status"] == "PASS")
        file_ok = (n_pass == 33 and not invalid)
        # duplicates alone don't fail the file, but are reported
        if n_pass != 33:
            overall_ok = False
        report["files"][path.name] = {
            "total": len(items), "chapters": len(chapters),
            "chapters_pass": f"{n_pass}/33",
            "valid_total": sum(pv.values()),
            "invalid_total": len(invalid),
            "duplicate_exact": dexact,
            "duplicate_near_sample": near,
            "invalid_sample": invalid[:20],
            "rows": rows,
            "status": "PASS" if n_pass == 33 else "FAIL",
        }
        print(f"{path.name}: total={len(items)} valid={sum(pv.values())} "
              f"invalid={len(invalid)} dup_exact={dexact} "
              f"chapters>={TARGET}: {n_pass}/33 -> {'PASS' if n_pass == 33 else 'FAIL'}")
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"Report: {OUT}")
    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
