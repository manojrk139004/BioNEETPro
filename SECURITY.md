# SECURITY.md — BioNEETPro V1 Security Model (release freeze)

## Authentication
- Firebase ID tokens verified server-side (`firebase_admin.auth.verify_id_token`).
- **Production fails closed by default**: `REQUIRE_FIREBASE_AUTH` unset (and no
  `DEV_AUTH_MODE`) = strict. Unverified callers get 401/403 — never a trusted
  caller-supplied `student_id`.
- **Development explicitly opts in**: `DEV_AUTH_MODE=true` (local runs, dev
  test-suite). Never set in production.
- Frontend attaches the Firebase ID token (`Authorization: Bearer`) on chat.

## Authorization
- Roles in V1: `student`, `admin` (verified `admin:true` claim or server-side
  `users/{uid}.role`). No TEACHER / SUPER_ADMIN / institution layer (N/A).
- Admin-only: `/api/tutor/tracker`, `/api/tutor/import-kaggle`,
  `/api/mcqs/generate`. Learner profile: self-or-admin. All writes
  (MCQ submit, flashcards, chat-thread delete) bind to the verified uid;
  mismatched body ids are rejected (403).
- Firestore rules mirror this (owner-only per-student docs; admin-only writes
  to `mcqs`/`videos`/`updates`/`admin`; `results` list requires sign-in).
- Full matrix: `docs/ENDPOINT_AUTHORIZATION_MATRIX.md`.

## Persistence
- Firestore-first via `firestore_store.py`; local JSON is a dev fallback.
- Strict mode: authenticated writes require live Firestore (`require_store`),
  else explicit 503 — never silent local writes on ephemeral disk.

## Input / abuse controls
- 256 KB body cap; message/query/history/context/pagination clamps; integer and
  range validation on stepper/quiz/MCQ inputs.
- Process-local in-memory IP rate limiting on `/chat`, `/ask`,
  `/api/tutor/answer` (Redis = documented future work for multi-instance).
- Errors are user-safe strings; no traces, secrets, tokens, or paths.
- Tutor output sanitized (escape-first Markdown, safe links only); XSS-tested
  against the shipped formatter.

## BKT invariant
Mastery is clamped to [0.01, 0.99] (intentional — avoids absorbing states);
repeated correct evidence approaches 0.99, never exceeds it.

## Secrets
- Never in source: `.env`, `.env.local`, `serviceAccount.json` are gitignored
  and excluded from the audit ZIP; `.env.example` holds placeholders only.
- The `AIza...` key in `BioNeet-Pro.html` is the public Firebase *web client*
  key (public by design; protected by Auth + security rules).
- Standing advisory: real dev credentials exist on the maintainer machine —
  MANUAL CREDENTIAL ROTATION REQUIRED if ever exposed beyond it.

## Known limitations
- Rate limiting is per-process (single-instance appropriate).
- Docker runtime verification pending (no daemon on audit machine).
- Expired-token mint test NOT VERIFIED (no mintable test key); invalid-token
  rejection verified behaviorally.
