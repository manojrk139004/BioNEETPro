# PART 5+6 — Retrieval & NLP forensics (actual code, not comments)

## Retrieval (`retrieval_engine.py`)

- Sources: KB CSV + textbook chunks, separate TF-IDF vectorizers (`ngram (1,2)`, english stopwords, max_features 8000/12000).
- Formula per candidate: `score = 0.35·cosine + 0.25·canonical + 0.15·keyword + 0.10·section + 0.05·context + 0.05·chapter + 0.05·graph`
  (`WEIGHTS`, line 43; applied lines 168–229 KB / 296–358 textbook).
- Post-pass (beast layer): BM25-style rarity boost (≤0.12) + canonical-title bonus (+0.04) — `_bm25_boost`, `_single_search`.
- Thresholds: reject `<0.12`, LOW `0.12–0.16`, MEDIUM `0.16–0.30`, HIGH `≥0.30` (lines 39–41).
  `tutor_engine` enforces the same 0.12 cutoff (line 193). No learned semantic similarity — **lexical only** (no embeddings).
- Comparison: `COMPARISON_RE` + `BARE_VS_RE` split (`split_comparison`), both sides retrieved, interleaved, flagged `is_comparison` + `compare_terms`; short forms expanded (`C3→Calvin`, `C4→Kranz`).
- Rejection: below-cutoff or concept-mismatch → controlled refusal, never nearest-neighbor.
- Verdict: genuinely hybrid lexical retrieval with calibrated gates; failure mode is vocabulary mismatch (fixed per-term via aliases), not math.

## NLP (`nlp_pipeline.py`, `concept_normalizer.py`, `syllabus.py`)

- Normalization: shorthand map (~35 rules: abt→about, b/w→between), typo map (~20: mitocondria→mitochondria), punctuation clean. Live-verified: "teach me abt cell"→Cell, "mitocondria powrhouse"→Mitochondria.
- Intent: **10 ordered regexes** (`INTENT_PATTERNS`, lines 196–215): mcq_request, difference_comparison, why, how_process, function, example, revision, follow_up, overview_explanation, definition; first match wins @0.92 else general_doubt@0.70. Rule-based, not ML.
- Concepts: ~260 hand aliases (`concept_normalizer.CONCEPT_ALIASES`) + dynamic index-derived entries; longest-match wins. Live failure example: "compare xylem vs phloem…" → canonical "Electron Transport System" (token "transport" over-matched) and retrieved Respiration chunk 12.4.2 — genuine misroute, recorded.
- Syllabus gate: banned-domain reject → chapter-keyword hit → generic-word hit → normalizer hit → textbook-rarity fallback (word len≥5 in 1–15 chunks). Live: Newton/python/cricket/molarity/gibberish/empty all REJECTED; SA-node/IUDs/countercurrent false-refusals were fixed by adding keywords.
- Bloom: keyword-mapped BT1–BT6 (`BLOOM_KEYWORDS`), default BT2.
- Anaphora: 4 hardcoded patterns (nlp_pipeline.py:248–283). Verdict: primarily keyword/rule-driven with verified behavior on tested patterns; NOT a general NLU.
