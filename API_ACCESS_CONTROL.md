# API_ACCESS_CONTROL.md — Route Classification (verified 2026-09-05)

`REQUIRE_FIREBASE_AUTH=false` (default, local dev): header identity honored when
present; body/query id otherwise. `=true` (production): only verified Firebase ID
tokens honored; everything else 401. Tests: `tests/test_security_regression.py`.

## PUBLIC (no auth, rate-limited where expensive)
| Route | Auth | Rate-limit | Notes |
|---|---|---|---|
| `GET /health`, `GET /api/health` | no | no | liveness, no AI calls |
| `GET /api/ready` | no | no | readiness (engine + pool>=100) |
| `POST /chat`, `POST /ask` | no | YES | friendly errors, no stack traces |
| `POST /api/tutor/query|step|verify` | no | no | stepper; strict input types/ranges |
| `GET /api/tutor/dataset-info` | no | no | corpus metadata only, no private data |
| `GET /api/syllabus` | no | no | static syllabus |
| `GET /api/mcqs/seed` | no | no | static MCQ bank page (limit clamped 1..200) |
| `GET /api/textbook/chapters`, `GET /api/textbook/pdf/<id>` | no | no | map-lookup only (traversal-safe), 404 JSON |
| `GET /api/safety/metrics` | no | no | aggregate safety counters |

## AUTHENTICATED STUDENT (identity-bound; 401/403 on mismatch)
| Route | Rule |
|---|---|
| `POST /api/tutor/answer`, `POST /api/tutor/answer/stream` | rate-limited; invalid credential -> anonymous, never spoofed |
| `POST /api/mcq/generate|submit|submit-batch` | attempts recorded under caller id; submit-batch capped 100, time 0..3600s |
| `GET /api/learner/profile` | self-only unless admin (header id vs query id enforced) |
| `GET /api/learner/review-due`, `/api/score/predict|history`, `/api/coach/tip` | caller id only |
| Flashcards CRUD + `GET|DELETE /api/chat/thread` | caller id only |

## ADMIN (verified admin only; anonymous -> 401/403)
- `GET /api/tutor/tracker` (limit clamped 1..100)
- `POST /api/tutor/import-kaggle` (errors clamped, no trace leak)
- `POST /api/mcqs/generate` (count clamped 1..50; subprocess runs generator)

Admin proof: verified token `admin:true` claim OR server-side `users/{uid}.role=="admin"`
(read via Admin SDK — never client input). Firestore rules mirror this
(`firestore.rules`: owner-only per-student docs, public MCQ/video/update reads,
admin-only writes, `results` list requires sign-in).

## INPUT VALIDATION / ERROR HANDLING
- Global `MAX_CONTENT_LENGTH` 256 KB (env `MAX_CONTENT_LENGTH_BYTES`).
- Message/query caps (3000 chars), history capped (8 turns x 1500 chars),
  context fields capped (160 chars), pagination clamped.
- All error responses are short user-safe strings; diagnostics go to server logs
  only (no tokens/keys/student data in logs).
- Rate limiter is in-memory per-process (documented; Redis upgrade path in
  DEPLOYMENT_NOTES.md).
