# docs/TUTOR_BEHAVIOR_CONTRACT.md — Binding Tutor Rules (V1)

## RULE 1 — Current explicit user intent has highest priority
A query naming its own Biology topic determines WHAT is taught. History must
never silently replace it. ("Teach me flowers." → flowers. Period.)

## RULE 2 — Conversational context is preserved for genuine follow-ups
Pronoun/bare follow-ups with NO explicit topic ("make it simpler", "what does
it do?", "why?", "explain that again") inherit the focal concept.

## RULE 3 — Explicit topic switch resets topic context
"Explain cardiac cycle." → "Now teach me flower and its parts." → flower.
Generalizes to ANY topic pair, ANY phrasing carrying explicit topic evidence.

## RULE 4 — Learner model personalizes HOW, not WHAT
Mastery/weakness may change depth, difficulty, examples, tips. It must never
select or replace the requested topic. (Verified by contamination tests.)

## RULE 5 — Retrieval must follow current intent
Resolved retrieval queries must not contain stale topics unless the current
query is a genuine topic-less follow-up.

## RULE 6 — Evidence must match the answer
Chapter/topic labels, citations, and explanation must agree with each other
AND with the current user query. (Enforced by fixing the source — query
resolution — plus alignment tests.)

## RULE 7 — Unknown/out-of-scope handled honestly
No confident unrelated answers: clarification or uncertainty-flagged
best-effort. Existing out-of-syllabus refusal behavior preserved.

## RULE 8 — No keyword patches, ever
Topic correctness must flow through general machinery (entity extraction,
canonical vocabulary, syllabus keyword index, retrieval ranking). Any fix of
the form `if "<topic>" in query` is a contract violation.

## Operational definitions
- "Explicit topic evidence": non-empty `extract_biology_entities()`, or a
  canonical concept match, or a syllabus-valid verdict with real
  `matched_keywords` — all pre-existing general mechanisms.
- "Genuine follow-up": no explicit topic evidence + (pronoun reference or
  bare continuation phrase).
- Context priority: (1) current explicit intent → (2) immediate reference →
  (3) conversation history → (4) learner personalization →
  (5) general recommendations.
