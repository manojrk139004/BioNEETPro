# PART 14 — Requirement matrix (evidence in `30_runtime_results.md`, code in `10_source/`)

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| 1 | Biology-only behavior | GREEN | Newton/python/cricket/molarity/gibberish/empty all REJECTED live |
| 2 | Syllabus restriction | YELLOW | Works, but keyword-list architecture needed per-term patches (earthworm/SA-node/IUDs cases) + rarity fallback |
| 3 | NCERT-grounded knowledge | GREEN | 774 chunks + 158 KB rows; citations on replies |
| 4 | Local textbook ingestion | GREEN | `ncert_ingestion.py`, committed index + checksums |
| 5 | Textbook chunking | GREEN | Section-aware ~200-word chunks |
| 6 | Page-aware traceability | GREEN | Page/section/chunk_id cited live (e.g. Ch18 Sec 18.4.3 p237) |
| 7 | NLP normalization | GREEN | "abt", "mitocondria", "ATP!!!" resolved live |
| 8 | Intent detection | YELLOW | 10 regexes; "I got question 2 wrong" → mcq_request misfire |
| 9 | Concept extraction | YELLOW | Dict-based; "xylem vs phloem" → "Electron Transport System" misroute verified |
| 10 | Concept normalization | YELLOW | ~260 hand aliases, no embeddings; needs per-term maintenance |
| 11 | Broad-vs-specific retrieval | YELLOW | Canonical boost + pair search exist; long queries can misroute (see #9) |
| 12 | Hybrid retrieval | GREEN | TF-IDF+keyword+canonical+section+context+chapter+graph, dual corpus |
| 13 | Confidence gating | GREEN | 0.12/0.16/0.30 tiers + REJECTED path, enforced in both tutors |
| 14 | Conversational context | GREEN | 3/3 reference resolutions live (it/folds/that) |
| 15 | Pronoun resolution | YELLOW | Works on tested patterns; only 4 hardcoded patterns; bare "why?" refused |
| 16 | Learner context | GREEN | Mastery drives strategy selection |
| 17 | Learner mastery | GREEN | BKT 0.50/0.15/0.10/0.25, concept/chapter/topic levels |
| 18 | Repeated mistake detection | YELLOW | Implemented + de-escalation; 4-mistake escalation not runtime-verified |
| 19 | Adaptive tutoring | YELLOW | 6 strategies real, but analogy pool has 12 entries with stale keys (c11/c12/c16/c18) |
| 20 | Personalized MCQs | YELLOW | Adaptive difficulty + weak-topic mode verified; "five"→default-5 (digits-only regex); no-history weak-topics falls back honestly |
| 21 | MCQ validation | GREEN | 4-distinct-options + index + answer-match enforced |
| 22 | Difficulty handling | GREEN | Override + adaptive verified (genetics→hard/user_override) |
| 23 | Bloom information | YELLOW | Heuristic BT tags; 8767-row blooms dataset dormant, zero references |
| 24 | Concept graph usage | YELLOW | 97 edges loaded, +0.05 bonus, neighbors displayed; no multi-hop reasoning in answers |
| 25 | Grounded AI API generation | GREEN | Evidence-pack RAG + cite-or-refuse + model chain; 25/29 probes api_grounded |
| 26 | Local response validation | GREEN | Faithfulness proxy + warning on both paths |
| 27 | Local-first functionality | YELLOW | Template path exists and served 34 probes in gate; offline explicitly untested here |
| 28 | Multi-user separation | GREEN | Independent profiles verified (user B mastery 0.5) |
| 29 | Evaluation | GREEN | 98-Q golden + beast eval + committed results |
| 30 | Regression testing | GREEN | 17+5+6 unittest suites, all passing at audit time |

**Coverage: 18 GREEN (60%), 12 YELLOW (40%), 0 RED. Weighted ≈80%.**
