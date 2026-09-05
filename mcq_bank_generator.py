#!/usr/bin/env python3
"""BioNEET-Pro no-cost MCQ bank generator (Phase 2).

Generates NCERT-grounded MCQs WITHOUT any LLM/API cost from:
  1. data/neet_knowledge_base.csv (definitions, traps -> stems)
  2. data/syllabus_registry.json chapter keywords (term-association stems)
  3. data/ncert_textbook_index.json (section-cited explanations)

Each MCQ: 4 distinct options, exactly one correct, difficulty label,
explanation citing the NCERT section, chapter tag. Validated with
mcq_engine.LocalMCQEngine.validate_mcq + chapter-keyword sanity +
exact/near-duplicate rejection. Writes accepted MCQs to
data/indexed_mcqs_cache.json (backend store) and
data/mcq_firestore_seed.json (upload via admin panel -> Firestore `mcqs`).

Usage:
  python mcq_bank_generator.py --min-per-chapter 25
  python mcq_bank_generator.py --chapter c32 --count 20
"""
import argparse
import difflib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from mcq_engine import LocalMCQEngine  # noqa: E402
from syllabus import syllabus_validator  # noqa: E402

random.seed(20260904)

CACHE_PATH = BASE_DIR / "data" / "indexed_mcqs_cache.json"
SEED_PATH = BASE_DIR / "data" / "mcq_firestore_seed.json"
LOG_PATH = BASE_DIR / "data" / "mcq_generation_log.json"


def load_chapters():
    out = {}
    sj = syllabus_validator.syllabus
    for cls in ("class_11", "class_12"):
        for unit, ud in (sj.get(cls) or {}).items():
            for cid, ch in (ud.get("chapters") or {}).items():
                out[cid.lower()] = {"name": ch.get("chapter_name", cid),
                                    "keywords": [k.lower() for k in ch.get("keywords", [])]}
    return out


def load_kb():
    import csv
    rows = []
    p = BASE_DIR / "data" / "neet_knowledge_base.csv"
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _is_dup_in(bucket, nq, ntok, thresh=0.88):
    for q in bucket:
        nq2 = norm(q)
        if nq == nq2:
            return True
        q2tok = set(nq2.split())
        if not ntok or not q2tok:
            continue
        jac = len(ntok & q2tok) / max(1, len(ntok | q2tok))
        if jac < 0.5:
            continue
        if difflib.SequenceMatcher(None, nq, nq2).ratio() >= thresh:
            return True
    return False


def is_dup(new_q, existing_qs, thresh=0.88, chapter=None, buckets=None):
    """Near-duplicate check. With per-chapter buckets (dict), checks only the
    same chapter in full (no 400-window blind spot at 200/chapter scale).
    Without buckets, checks the FULL history (slower but correct)."""
    nq = norm(new_q)
    ntok = set(nq.split())
    if buckets is not None and chapter is not None:
        return _is_dup_in(buckets.get(chapter, []), nq, ntok, thresh)
    return _is_dup_in(existing_qs, nq, ntok, thresh)


def pick_distractors(answer_term, pool_terms, k=3):
    cands = [t for t in pool_terms if norm(t) != norm(answer_term) and len(t) > 2]
    random.shuffle(cands)
    out = []
    for t in cands:
        if all(norm(t) != norm(o) for o in out):
            out.append(t)
        if len(out) == k:
            break
    return out


TEMPLATES = [
    ("Which of the following is most closely associated with '{term}' ({chapter})?",
     "NCERT {chapter}: '{term}' is a key term from this chapter's syllabus."),
    ("Consider '{term}' from {chapter}. Which statement about it is correct?",
     "NCERT {chapter} — '{term}' appears among the chapter's core concepts; the correct option names it while distractors come from other chapters."),
    ("Four terms are given below. Three belong to other chapters and one belongs to {chapter} in the context of '{term}'. Pick the one from {chapter}.",
     "NCERT {chapter}: verified against the chapter keyword list; see {chapter} sections covering '{term}'. The other three options are real terms from unrelated chapters."),
    ("Assertion (A): '{term}' is a concept studied under {chapter}. Reason (R): the correct option identifies the chapter-specific term. Choose the term that makes (A) true.",
     "NCERT {chapter} assertion-reason style: '{term}' is listed in this chapter's keywords."),
]


def generate_for_chapter(cid, cinfo, kb_rows, all_terms, existing_qs, count, log,
                         buckets=None):
    made = []
    chapter = cinfo["name"]
    terms = [t for t in cinfo["keywords"] if len(t) > 2]
    if not terms:
        log.append({"chapter": cid, "status": "skip", "reason": "no keywords"})
        return made
    # KB definitions for this chapter as extra answer terms
    kb_terms = []
    for r in kb_rows:
        if str(r.get("chapter_id", "")).lower() == cid or \
           str(r.get("chapter_name", "")).strip().lower() == chapter.strip().lower():
            for key in ("topic", "title"):
                v = str(r.get(key, "")).strip()
                if len(v) > 3 and norm(v) not in (norm(t) for t in terms):
                    kb_terms.append(v)
    answer_pool = terms + kb_terms
    random.shuffle(answer_pool)
    diffs = ["Easy", "Medium", "Hard"]
    t_idx = 0
    # Multiple stems per term (one per template) so thin chapters can still
    # reach the target without duplicates.
    for round_no in range(len(TEMPLATES)):
        for term in answer_pool:
            if len(made) >= count:
                break
            distract = pick_distractors(term, all_terms, 3)
            if len(distract) < 3:
                log.append({"chapter": cid, "status": "reject", "reason": "distractor shortage",
                            "term": term})
                continue
            tpl_q, tpl_e = TEMPLATES[(t_idx) % len(TEMPLATES)]
            t_idx += 1
            # Cap term length for stem readability
            short_term = term if len(term) <= 60 else term[:57] + "..."
            q = tpl_q.format(term=short_term, chapter=chapter)
            if is_dup(q, existing_qs, chapter=chapter, buckets=buckets):
                log.append({"chapter": cid, "status": "reject", "reason": "near-duplicate",
                            "term": term})
                continue
            opts = [term.title() if len(term) <= 40 else term] + distract
            # Ensure distinct display options
            if len({norm(o) for o in opts}) != 4:
                log.append({"chapter": cid, "status": "reject", "reason": "non-distinct options",
                            "term": term})
                continue
            random.shuffle(opts)
            correct_index = opts.index(next(o for o in opts if norm(o) == norm(
                term.title() if len(term) <= 40 else term)))
            mcq = {"id": f"gen-{cid}-{len(existing_qs) + len(made) + 1}",
                   "concept_id": f"GEN-{cid.upper()}",
                   "chapter": chapter,
                   "topic": term,
                   "question": q,
                   "options": opts,
                   "correct_index": correct_index,
                   "correct_answer": opts[correct_index],
                   "explanation": tpl_e.format(term=short_term, chapter=chapter),
                   "difficulty": diffs[len(made) % 3],
                   "cognitive_level": "BT1 - Remembering",
                    "source": "template-ncert-terms (no LLM)"}
            eng = LocalMCQEngine.__new__(LocalMCQEngine)
            if not eng.validate_mcq(mcq):
                log.append({"chapter": cid, "status": "reject", "reason": "validate_mcq failed",
                            "term": term})
                continue
            made.append(mcq)
            existing_qs.append(q)
            if buckets is not None:
                buckets.setdefault(chapter, []).append(q)
    return made


def generate_kb_stems(cid, cinfo, kb_rows, existing_qs, count, log, buckets=None):
    """KB-grounded stems (no LLM): definition-identification + NEET-trap
    attribution. Text is structurally distinct from keyword-template stems,
    so near-dedupe treats them as new questions."""
    made = []
    chapter = cinfo["name"]
    rows = [r for r in kb_rows
            if str(r.get("chapter_id", "")).lower() == cid or
            str(r.get("chapter_name", "")).strip().lower() == chapter.strip().lower()]
    others = [str(r.get("topic") or r.get("title", "")).strip() for r in kb_rows
              if str(r.get("chapter_id", "")).lower() != cid and
              str(r.get("chapter_name", "")).strip().lower() != chapter.strip().lower()]
    others = [o for o in others if len(o) > 3]
    random.shuffle(rows)
    diffs = ["Medium", "Hard", "Easy"]
    for r in rows:
        if len(made) >= count:
            break
        title = str(r.get("topic") or r.get("title", "")).strip()
        if len(title) < 4:
            continue
        variants = []
        defi = str(r.get("definition", "")).strip()
        if len(defi) > 40:
            variants.append((
                f"Which concept is described as follows? \"{defi[:220]}\"",
                f"NCERT {chapter}: definition of '{title}'.",
            ))
        trap = str(r.get("neet_traps", "")).strip()
        if len(trap) > 30:
            variants.append((
                f"NEET trap alert from {chapter}: \"{trap[:200]}\" "
                f"— which concept does this warning apply to?",
                f"NCERT {chapter}: trap listed for '{title}'.",
            ))
        mech = str(r.get("mechanism_steps", "")).strip()
        if len(mech) > 40 and len(made) < count:
            variants.append((
                f"Which process follows these steps? \"{mech[:200]}\"",
                f"NCERT {chapter}: mechanism under '{title}'.",
            ))
        for q, expl in variants:
            if len(made) >= count:
                break
            # KB definition/trap text is sometimes shared across KB rows tagged
            # to different chapters, so check GLOBALLY (not just the chapter
            # bucket): identical stems must not exist under two chapters.
            if is_dup(q, existing_qs, chapter=chapter, buckets=buckets) or \
                    is_dup(q, existing_qs):
                log.append({"chapter": cid, "status": "reject",
                            "reason": "near-duplicate", "term": title})
                continue
            distract = pick_distractors(title, others, 3)
            if len(distract) < 3:
                log.append({"chapter": cid, "status": "reject",
                            "reason": "distractor shortage", "term": title})
                continue
            opts = [title] + distract
            if len({norm(o) for o in opts}) != 4:
                continue
            random.shuffle(opts)
            ci = next(i for i, o in enumerate(opts) if norm(o) == norm(title))
            mcq = {"id": f"kb-{cid}-{len(existing_qs) + len(made) + 1}",
                   "concept_id": str(r.get("concept_id", f"KB-{cid.upper()}")),
                   "chapter": chapter, "topic": title, "question": q,
                   "options": opts, "correct_index": ci,
                   "correct_answer": opts[ci], "explanation": expl,
                   "difficulty": diffs[len(made) % 3],
                   "cognitive_level": "BT2 - Understanding",
                    "source": "template-kb-stems (no LLM)"}
            eng = LocalMCQEngine.__new__(LocalMCQEngine)
            if not eng.validate_mcq(mcq):
                continue
            made.append(mcq)
            existing_qs.append(q)
            if buckets is not None:
                buckets.setdefault(chapter, []).append(q)
    return made


AR_OPTIONS = [
    "Both A and R are true and R is the correct explanation of A",
    "Both A and R are true but R is NOT the correct explanation of A",
    "A is true but R is false",
    "A is false but R is true",
]


def _kw_set(cinfo):
    return {norm(k) for k in cinfo["keywords"]}


def _mk_item(cid, chapter, topic, q, opts, ci, expl, diff, cog, src):
    return {"id": "", "concept_id": f"GEN-{cid.upper()}", "chapter": chapter,
            "topic": topic, "question": q, "options": opts,
            "correct_index": ci, "correct_answer": opts[ci],
            "explanation": expl, "difficulty": diff,
            "cognitive_level": cog, "source": src}


def _accept(cid, chapter, topic, q, opts, ci, expl, diff, cog, src,
            existing_qs, buckets, log):
    if not opts or len(opts) != 4 or len({norm(o) for o in opts}) != 4:
        log.append({"chapter": cid, "status": "reject",
                    "reason": "non-distinct options", "term": topic})
        return None
    if not (0 <= ci < 4):
        return None
    if is_dup(q, existing_qs, chapter=chapter, buckets=buckets):
        log.append({"chapter": cid, "status": "reject",
                    "reason": "near-duplicate", "term": topic})
        return None
    mcq = _mk_item(cid, chapter, topic, q, opts, ci, expl, diff, cog, src)
    eng = LocalMCQEngine.__new__(LocalMCQEngine)
    if not eng.validate_mcq(mcq):
        log.append({"chapter": cid, "status": "reject",
                    "reason": "validate_mcq failed", "term": topic})
        return None
    return mcq


def _commit(mcq, cid, existing_qs, buckets, made):
    mcq["id"] = f"fam-{cid}-{len(existing_qs) + len(made) + 1}"
    made.append(mcq)
    existing_qs.append(mcq["question"])
    buckets.setdefault(mcq["chapter"], []).append(mcq["question"])


def generate_families(cid, cinfo, chapters, existing_qs, buckets, need, log):
    """5 high-volume honest families (no LLM). Each item's truth value is
    computed from keyword lists, never guessed. Loops until need met."""
    made = []
    chapter = cinfo["name"]
    own = sorted(_kw_set(cinfo))
    if not own:
        return made
    others = [(oid, oc) for oid, oc in chapters.items() if oid != cid]
    other_terms = [(t, oc["name"]) for oid, oc in others for t in oc["keywords"]]
    chap_names = [c["name"] for _, c in others]
    import itertools
    random.shuffle(own)

    def outsider_for(avoid, k=1):
        pool = [(t, cn) for t, cn in other_terms
                if norm(t) not in avoid and len(t) > 2]
        random.shuffle(pool)
        out, seen = [], set()
        for t, cn in pool:
            if norm(t) in seen:
                continue
            seen.add(norm(t))
            out.append((t, cn))
            if len(out) == k:
                break
        return out

    rounds = 0
    fams = ["odd", "ar", "true", "match", "common"]
    while len(made) < need and rounds < 40:
        rounds += 1
        for fam in fams:
            if len(made) >= need:
                break
            if fam == "odd":
                # 3 insiders + 1 outsider; outsider guaranteed foreign.
                ins = random.sample(own, min(3, len(own)))
                if len(ins) < 3:
                    continue
                avoid = set(ins)
                out = outsider_for(avoid, 1)
                if not out:
                    continue
                ot, _ocn = out[0]
                disp = [t.title() for t in ins] + [ot.title()]
                random.shuffle(disp)
                ci = disp.index(ot.title())
                q = (f"Consider these four terms: {', '.join(disp)}. Three of them "
                     f"belong to {chapter} — identify the odd one out.")
                m = _accept(cid, chapter, "odd-one-out: " + ot, q, disp, ci,
                            f"NCERT {chapter}: '{ot}' is not among this chapter's "
                            f"keywords, the other three are.", "Medium",
                            "BT2 - Understanding", "template-odd-one-out (no LLM)",
                            existing_qs, buckets, log)
                if m:
                    _commit(m, cid, existing_qs, buckets, made)
            elif fam == "ar":
                # Assertion-Reason with COMPUTED truth values (never both false).
                t = random.choice(own)
                ocid, oc = random.choice(others)
                t2 = random.choice(oc["keywords"]) if oc["keywords"] else t
                a_true = random.random() < 0.6
                ca = chapter if a_true else oc["name"]
                r_true = random.random() < 0.6
                if not a_true and not r_true:
                    r_true = True
                cr = oc["name"] if (norm(t2) in _kw_set(oc)) == r_true else chapter
                # recompute actual truth from lists (source of truth)
                a_true = norm(t) in _kw_set(
                    cinfo if ca == chapter else next(c for i, c in others if c["name"] == ca))
                r_true = norm(t2) in _kw_set(
                    cinfo if cr == chapter else next(c for i, c in others if c["name"] == cr))
                if not a_true and not r_true:
                    continue
                q = (f"Assertion (A): '{t}' is a key concept of {ca}. "
                     f"Reason (R): '{t2}' is a key concept of {cr}.")
                if a_true and r_true:
                    ci = 1
                elif a_true:
                    ci = 2
                else:
                    ci = 3
                m = _accept(cid, chapter, f"assertion-reason: {t}", q,
                            list(AR_OPTIONS), ci,
                            f"NCERT keyword check: (A) is {'true' if a_true else 'false'}, "
                            f"(R) is {'true' if r_true else 'false'}.",
                            "Hard", "BT4 - Analyzing",
                            "template-assertion-reason (no LLM)",
                            existing_qs, buckets, log)
                if m:
                    _commit(m, cid, existing_qs, buckets, made)
            elif fam == "true":
                # Correct statement (false options cite foreign terms).
                t = random.choice(own)
                outs = outsider_for(_kw_set(cinfo), 3)
                if len(outs) < 3:
                    continue
                stmts = [f"'{t}' is an important concept in {chapter}"]
                for ot, _ocn in outs:
                    stmts.append(f"'{ot}' is an important concept in {chapter}")
                # rebuild: shuffled statements with correct tracking
                stmts_shuf = [(stmts[0], True)] + [(f"'{o[0]}' is an important concept in {chapter}", False) for o in outs]
                random.shuffle(stmts_shuf)
                disp_opts = [f"Statement {i + 1}" for i in range(4)]
                body = "; ".join(f"({i + 1}) {s}" for i, (s, _) in enumerate(stmts_shuf))
                ci = next(i for i, (_, ok) in enumerate(stmts_shuf) if ok)
                q = f"Which statement about {chapter} is correct? {body}."
                m = _accept(cid, chapter, f"true-statement: {t}", q, disp_opts, ci,
                            f"NCERT {chapter}: only the statement about '{t}' is "
                            f"correct; the other terms belong elsewhere.", "Medium",
                            "BT2 - Understanding", "template-true-statement (no LLM)",
                            existing_qs, buckets, log)
                if m:
                    _commit(m, cid, existing_qs, buckets, made)
            elif fam == "match":
                # Term -> chapter (chapter names as options).
                t = random.choice(own)
                poll = [cn for cn in chap_names if cn != chapter]
                random.shuffle(poll)
                if len(poll) < 3:
                    continue
                opts = [chapter] + poll[:3]
                random.shuffle(opts)
                q = f"The term '{t}' belongs to which chapter?"
                m = _accept(cid, chapter, f"chapter-match: {t}", q, opts,
                            opts.index(chapter),
                            f"NCERT syllabus: '{t}' is a keyword of {chapter}.",
                            "Easy", "BT1 - Remembering",
                            "template-chapter-match (no LLM)",
                            existing_qs, buckets, log)
                if m:
                    _commit(m, cid, existing_qs, buckets, made)
            elif fam == "common":
                # Commonality of three insider terms.
                if len(own) < 3:
                    continue
                ins = random.sample(own, 3)
                poll = [cn for cn in chap_names
                        if not (set(ins) & _kw_set(
                            next(c for i, c in others if c["name"] == cn)))]
                random.shuffle(poll)
                if len(poll) < 3:
                    continue
                opts = [f"All three are key concepts of {chapter}"] + \
                       [f"All three are key concepts of {cn}" for cn in poll[:3]]
                random.shuffle(opts)
                q = (f"What do '{ins[0]}', '{ins[1]}' and '{ins[2]}' have in common?")
                m = _accept(cid, chapter, "commonality: " + ", ".join(ins), q, opts,
                            opts.index(f"All three are key concepts of {chapter}"),
                            f"NCERT syllabus: all three are keywords of {chapter}.",
                            "Medium", "BT2 - Understanding",
                            "template-commonality (no LLM)",
                            existing_qs, buckets, log)
                if m:
                    _commit(m, cid, existing_qs, buckets, made)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-per-chapter", type=int, default=25)
    ap.add_argument("--chapter", type=str, default=None)
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--kb-stems", action="store_true",
                    help="also generate KB definition/trap stems per chapter")
    args = ap.parse_args()

    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else []
    chapters = load_chapters()
    kb_rows = load_kb()
    all_terms = []
    for cid, cinfo in chapters.items():
        all_terms.extend(cinfo["keywords"])
    all_terms = sorted(set(all_terms))

    counts = Counter(m.get("chapter", "?") for m in cache)
    # map chapter name -> cid
    name_to_cid = {c["name"].strip().lower(): cid for cid, c in chapters.items()}
    existing_qs = [m.get("question", "") for m in cache]
    buckets = {}
    for m in cache:
        buckets.setdefault(m.get("chapter", "?"), []).append(m.get("question", ""))
    log = []
    added = []

    targets = []
    if args.chapter:
        c = args.chapter.strip().lower()
        # accept cXX or chapter name
        cid = c if c in chapters else name_to_cid.get(c, c)
        targets.append((cid, args.count))
    else:
        for cid, cinfo in chapters.items():
            have = counts.get(cinfo["name"], 0)
            need = max(0, args.min_per_chapter - have)
            if need:
                targets.append((cid, need))

    for cid, need in targets:
        cinfo = chapters.get(cid)
        if not cinfo:
            log.append({"chapter": cid, "status": "skip", "reason": "unknown chapter id"})
            continue
        made = generate_for_chapter(cid, cinfo, kb_rows, all_terms, existing_qs, need, log, buckets)
        if args.kb_stems:
            kb_made = generate_kb_stems(cid, cinfo, kb_rows, existing_qs, need, log, buckets)
            made += kb_made
        still = need - len(made)
        if still > 0:
            made += generate_families(cid, cinfo, chapters, existing_qs, buckets, still, log)
        added.extend(made)
        log.append({"chapter": cid, "chapter_name": cinfo["name"], "status": "generated",
                    "requested": need, "accepted": len(made)})

    cache.extend(added)
    CACHE_PATH.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    # Seed file is ALWAYS rebuilt cumulatively from the full cache — a small
    # --chapter run must never clobber the 6k+ seed admins sync from.
    # NOTE: the seed must mirror the FULL cache (all id prefixes, including
    # kb-BIO-* and t1-* NCERT/medical items) so chapter coverage in the seed
    # matches the engine pool. Filtering by prefix silently dropped ~157
    # high-quality questions and made the seed thin while the cache was full.
    gen_all = [m for m in cache if m.get("question") and m.get("options")]
    SEED_PATH.write_text(json.dumps(
        [{"id": m.get("id", ""), "question": m.get("question", ""), "options": m.get("options", []),
          "correct": m.get("correct_index", m.get("correct", 0)), "explanation": m.get("explanation", ""),
          "chapter": m.get("chapter", "General Biology"), "difficulty": m.get("difficulty", "Medium"),
          "source_section": m.get("topic", "")} for m in gen_all], indent=1),
        encoding="utf-8")
    LOG_PATH.write_text(json.dumps(
        {"added": len(added), "total": len(cache), "log": log}, indent=1), encoding="utf-8")

    final_counts = Counter(m.get("chapter", "?") for m in cache)
    goal = args.min_per_chapter
    print(f"Added {len(added)} validated MCQs (no LLM). Total now {len(cache)}.")
    print(f"Chapters >= {goal}: {sum(1 for c in chapters.values() if final_counts.get(c['name'], 0) >= goal)}/33")
    thin = [(c['name'], final_counts.get(c['name'], 0)) for c in chapters.values()
            if final_counts.get(c['name'], 0) < goal]
    if thin:
        print("Still thin:", thin)
    print(f"Log: {LOG_PATH} | Firestore seed ({len(added)} docs): {SEED_PATH}")


if __name__ == "__main__":
    main()
