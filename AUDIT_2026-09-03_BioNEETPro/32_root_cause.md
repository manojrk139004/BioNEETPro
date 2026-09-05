# PART 15 — Root-cause analysis (YELLOW items only; zero RED)

1. **Syllabus false refusals** — `syllabus.py` keyword/generic lists (`:325-338`, chapter keywords).
   Any valid term absent from lists refuses unless the rarity fallback catches it. Fix: mine
   distinctive per-chapter terms from chunk text into keywords (as done for earthworm set).
2. **Intent misfire ("I got question 2 wrong" → mcq_request)** — `nlp_pipeline.py:197` pattern
   contains bare "question". Fix: require MCQ-count/topic context, add quiz-feedback intent.
3. **Concept misroute (xylem/phloem → ETS)** — TF-IDF cosine + token "transport" over-match;
   no semantic model. Fix: embedding reranker or transport-system disambiguation.
4. **Alias maintenance burden** — `concept_normalizer.CONCEPT_ALIASES` is hand-curated (~260).
   Fix: generate candidates from chunk concepts + human review.
5. **Pronoun coverage** — 4 patterns (`nlp_pipeline.py:248-283`). Fix: extend pattern set from log mining.
6. **Mistake escalation unverified** — needs 4 sequential wrong answers on one concept; code-reviewed only.
7. **Stale analogy keys** — `adaptive_tutor.py:49-63` uses pre-rationalization chapter codes
   (c11/c12/c16/c18); those analogies never fire. Fix: remap to c13/c14/c19/c21.
8. **Word-number quantities** — `mcq_engine.py:210` digits-only regex. Fix: word-to-number map.
9. **Dormant Bloom data** — wire `blooms_taxonomy_dataset.csv` to tagger or delete it.
10. **Graph underuse** — bonus 0.05 is negligible; neighbors display-only. Fix: inject neighbor context into evidence pack.
11. **Offline untested** — template path quality lower (earlier 58/98 offline measurement).

## Severity-ranked issues

- HIGH: (a) live answers depend on a free-tier provider (`agnes-2.0-flash`; `minimax-m3-free` verified dead, returns HTML); ~35% of calls fall back to templates; (b) unified-endpoint MCQ requests answered as text, not MCQs (`adaptive_tutor` ignores mcq intent; only `/chat` routes to `mcq_engine`); (c) wrong-chapter answers possible on long queries (verified xylem/phloem→Respiration).
- MEDIUM: stale analogy keys; digits-only quantities; no quiz-feedback handling; 150 MB+ dormant datasets; orphan `js/`+`css/`; live API key in `.env.local` (operational hygiene, redacted here).
- LOW: faithfulness proxy punishes good paraphrase (avg 0.525); `minimax` dead entry kept as last-resort chain item.
