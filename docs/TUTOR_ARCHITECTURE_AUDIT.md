# docs/TUTOR_ARCHITECTURE_AUDIT.md — Actual Implementation (traced 2026-09-05)

No idealization: every step below names the real module/function, verified by
instrumented reproduction of the reported failure
("can u teach me flower and its parts" after cardiac cycle → answered cardiac).

## 1. Current architecture
Single-brain RAG: `BioNeet-Pro.html` → `POST /chat|/ask|/api/tutor/answer`
(`app.py`) → `build_unified_answer()` → policy gate → `adaptive_tutor.
generate_tutoring_response()` → `_generate_inner()` → reply + citations.

## 2. Actual execution path (function-level)
1. Frontend `sendChat()` (`BioNeet-Pro.html`): sends `{message, history[-8:],
   context:{chapter,topic,goal}, student_id}` + Firebase ID token.
2. `app.ai_reply()` / `tutor_answer()` → `demo_ai_answer()` /
   `build_unified_answer(query, student_id, history, context)`.
3. Policy gate: `content_classifier.classify` → `policy_engine.evaluate`
   (block/allow). PDF intent (`_maybe_chapter_pdf_reply`) before tutoring.
4. `adaptive_tutor._generate_inner()`:
   a. `nlp_pipeline.process_query(query, history, student_id)` →
      `resolved_query`, `expanded_query`, `intent`, `focal_concept` (string),
      `biology_entities`, syllabus verdict.
   b. Intent branches: `mcq_request` (MCQ engine), `quiz_feedback/mcq_answer`
      (recent-MCQ review), syllabus-invalid (refusal).
   c. `retrieval_engine.search(resolved_query, expanded_query,
      focus_chapter_id, focal_context_name)` → ranked evidence (KB +
      textbook), rerank, confidence gate.
   d. `context_tracker.track_concept()` persists new focal concept.
   e. Learner profile → strategy/depth adaptation; guided-lesson / follow-up
      branches; API-grounded or local-fallback generation.
   f. `response_validator.validate_response()` → citations/figures/check-MCQ.
   g. `dialogue_state.record_turn()`; query logged to `tutor_query_log.jsonl`.

## 3. Context sources
- (a) Current raw query text. (b) `resolved_query` (anaphora-rewritten).
- (c) `history` (last 8 turns, frontend-supplied). (d) Tracker focal concept
  (`nlp_pipeline.ConversationContextTracker`, per-student, server-side).
- (e) Frontend `tutorContext` chapter/topic (sticky UI selection → backend
  `focus_chapter_id`). (f) Learner profile (mastery/weak topics).
- (g) `dialogue_state` turn counts/due reviews (memory, not retrieval input).

## 4. Priority of each context source (AS IMPLEMENTED — the defect)
`resolved_query` (history-spliced) outranks the raw current query: anaphora
rules 0–4 inject the focal concept into ANY query containing it/its/this/that
(`nlp_pipeline.resolve_conversational_anaphora` rule 4), with NO check whether
the current query names its own topic. Retrieval then faithfully ranks the
injected terms. Learner model affects depth only (correct). Focal/chapter
retrieval boosts are 0.05 each (cannot override explicit terms — verified).

## 5. Retrieval strategy
Dual-corpus TF-IDF (KB rows + 774 textbook chunks) + synonym/morph expansion,
comparison-pair split, BM25/title boosts, rare-term demotion, char fallback.

## 6. Ranking strategy
`hybrid_score` weighted sum (semantic .35, canonical .25, keyword .15,
section .10, context/chapter/graph .05 each) + rerank demotions. Top-1 wins;
empty → follow-up-from-focal attempt → controlled refusal.

## 7. Fallback strategy
`fallback_controller` on LOW confidence; local algorithmic reply when no AI
key; all fallbacks reuse the (possibly contaminated) resolved query — same
fix applies automatically once the query is clean.

## 8. Learner-model influence
Depth/difficulty/examples/tips only. Verified NOT a topic contaminator
(mastery never selects WHAT; tests in Phase 9 harness).

## 9. Dialogue-state behavior
Turn counting + due-review surfacing; does not feed retrieval text. Tracker
focal concept is the sticky topic pointer (overwritten every successful turn).

## 10. Frontend/backend interaction
Frontend owns: history window, sticky chapter/topic context, chat persistence
(Firestore `chat_threads`), MCQ click state. Backend owns: resolution,
retrieval, tracking, validation. Contract gap (minor): sticky UI chapter can
linger after a topic switch (0.05 boost only — documented, not fixed here).

## 11. Known failure modes (root-caused)
- F1 (CONFIRMED, fixed this sprint): anaphora splicing into topic-complete
  queries → wrong-topic answers. Class: query-understanding/context
  contamination. Evidence: resolved "flower…parts" → "flower and Cardiac
  Cycle parts"; clean-query counterfactual ranks flower top-4.
- F2 (latent, hardened): `focal_context_name` assumed string; tuple input
  crashes (`AttributeError`) — one-line `str()` coercion added.
- F3 (minor, documented): sticky frontend chapter context; negligible weight.

## 12. Recommended target architecture (implemented)
Explicit-topic guard: current query carrying its own topic evidence
(entities / canonical concept / syllabus keywords — all existing general
machinery) is never history-rewritten (contract Rules 1, 3). Topic-less
follow-ups keep full inheritance (Rule 2). Priority: explicit intent >
immediate reference > history > personalization (Rule: learner HOW not WHAT).
