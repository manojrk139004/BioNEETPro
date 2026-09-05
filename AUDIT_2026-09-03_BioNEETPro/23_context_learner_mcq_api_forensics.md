# PART 7+8+9+10 — Context, learner, MCQ, API forensics (with live evidence)

## Conversational context (Part 7 chain, live)

"Explain mitochondria." → Mitochondria/HIGH → "Why does it have folds?" → resolved to Mitochondria/HIGH →
"What does that increase?" → resolved (folds/cristae)/HIGH → "Give me 3 questions on it." →
**answered as TEXT (api_grounded, Mitochondria chunk), NOT as MCQs** → "I got question 2 wrong." →
mcq_request intent but `local_fallback/no_match/LOW` → "Explain it again." → Mitochondria/HIGH.
Context preserved 3/3 on references. Defects: (a) MCQ-via-`adaptive_tutor` path ignores mcq intent
(only `app.demo_ai_answer`, i.e. `/chat`, routes to `mcq_engine`); (b) "I got question 2 wrong" has no
quiz-answer handling anywhere — falls to no_match.

## Learner model

Per-student JSON (`data/student_profiles/<id>.json`), BKT `pL0=0.50/pT=0.15/pS=0.10/pG=0.25`
(`learner_model.py:31-34`); concept/chapter/topic mastery, difficulty + Bloom stats, repeated-mistake
escalation with de-escalation, trajectory stages, 50-event history. Separation verified live:
user B got independent mastery 0.5. Strategy selection uses mastery+mistakes (6 strategies).
Caveat: same-`student_id` focal state is shared across sessions by design (observed "3 questions on
this"→Cardiac Cycle from earlier probes under one SID) — correct per-user, not cross-user bleed.
Retrieval score is NOT used as mastery (separate BKT update on quiz verify) — verified in code.

## MCQ

`mcq_engine.generate_mcqs`: quantity regex is **digits-only** (`\d+`, line 210) so "five"→default 5
(verified: "five hard questions"→count 5, hard/user_override — override worked, quantity coincided);
weak-topic mode falls back to "Diagnostic Mixed Syllabus" with zero history (honest label, verified);
"context" topic ("on this") resolves via focal tracker. Validation (`validate_mcq`): 4 distinct options,
index 0–3, answer-text equality — enforced at ingest; pool = KB rows + test1.csv hard items.
Personalization verdict: difficulty adapts to mastery; topic adapts to focal/weak list; NOT deeply personal.

## AI API

Exists and is PRIMARY live: 25/29 chat probes returned `api_grounded`. Config:
base `https://router.bynara.id/v1` (key prefix `sk-nry-`), model chain `[agnes-2.0-flash, minimax-m3-free]`
(`adaptive_tutor._model_chain`). Sent per call: system prompt + ≤4 evidence chunks (title/source/section/
page/definition≤900/mechanism≤700/traps≤400/figure captions) + last 4 history turns (≤500 chars) + query;
max_tokens 900, temp 0.2. Learner profile is NOT sent (only strategy label derived from it). Textbook as a
whole is NEVER sent. Refuse rule: model returning CANNOT ANSWER / short / error → next model → local
template fallback (observed 34%). `minimax-m3-free` returns an HTML error page (verified live) — dead route,
kept as last resort. `fallback_controller` (external emergency mode) is default-OFF and never fired
(empty audit log). Secrets: `.env.local` holds live key — REDACTED everywhere in this package.
