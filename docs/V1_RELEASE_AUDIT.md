# docs/V1_RELEASE_AUDIT.md — Hardening Audit (2026-09-05, release freeze)

Scope: SECURITY + CORRECTNESS + DEPLOYMENT + VERIFICATION. No V2+ features.
Prior verified systems (6600 MCQs, RAG, guardrails, Gunicorn config) preserved.

## 1. Authentication: fail closed — PASS
`is_strict_auth()` (single source of truth, per-request): strict unless
`DEV_AUTH_MODE=true` or legacy explicit `REQUIRE_FIREBASE_AUTH=false`.
Module default flipped from open to strict. Evidence:
`tests/test_v1_security_hardening.py` (tests 1–4) + prior
`tests/test_security_regression.py` (11/11).

## 2. Identity: never trust client — PASS
`resolve_identity()` binds all authenticated writes (MCQ submit/batch,
flashcards CRUD, chat-thread delete) to verified/header uid; mismatched body
ids → 403; strict-anon → 401. Learner profile self-or-admin. Evidence: tests
5–8 (403s + B-profile untouched assertion).

## 3. Endpoint matrix — PASS
37 routes inventoried in `docs/ENDPOINT_AUTHORIZATION_MATRIX.md`. TEACHER /
SUPER_ADMIN / institution: N/A — NOT PRESENT IN V1 (not created).

## 4. MCQ security — PASS
Submit paths identity-bound; generation/import admin-only; rate/size/type
validation intact. Tests 7–10.

## 5. Firestore prod behavior — PASS
`require_firestore()` + `require_store()` gate strict writes → explicit 503,
verified with zero local-file side effects; dev fallback preserved + tested.

## 6. BKT ceiling — PASS (answer B: intentional)
`learner_model.py:46,56` and `tutor_engine.py:100,110` clamp mastery to
[0.01, 0.99] (standard absorbing-state avoidance). Test proves approach
(≥0.85 after streak) and cap (never >0.99).

## 7. Docker — NOT VERIFIED (runtime)
Dockerfile statically verified (`test_12`); no daemon on audit machine, so
`docker build/run` NOT claimed. Exact commands in DEPLOYMENT.md.

## 8. Health — PASS
`/health`, `/api/health`, `/api/ready` tested: 200s, no secrets/traces/paths.

## 9. Secrets — PASS (with standing advisory)
No hard-coded secrets in source (`sk-*` hits are prefix checks/redaction
regexes; `AIza...` is the public web key). `.env*`/`serviceAccount.json`
gitignored + ZIP-excluded. Real dev credentials exist on maintainer disk:
MANUAL ROTATION REQUIRED if ever exposed.

## 10. CORS — PASS
Echo-only configured origins (evil origin gets no `*`); localhost strings are
dev defaults/test/docs; `app.run(127.0.0.1)` is dev-only (gunicorn in prod).

## 11. Rate limiting — PASS (documented limits)
In-memory per-process on expensive AI routes; 429 behaviorally tested. No
distributed protection claimed; Redis = future work.

## 12. Safe errors — PASS
404/400 probes contain no traces/paths; provider errors clamped.

## 13. AI regression — see final suite run (guardrails/injection suites).
## 14. Data integrity — verifier re-run in final pass (6600/6600/0/33/33).
## 15. Markdown/XSS — real-formatter node tests re-run in final pass.
