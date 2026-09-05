# docs/ENDPOINT_AUTHORIZATION_MATRIX.md — V1 Endpoint Inventory (verified 2026-09-05)

Auth model: production (default) is STRICT — only verified Firebase ID tokens
(`firebase_admin.auth.verify_id_token`) are honored; caller-supplied ids are
never trusted (401/403, fail closed). Development explicitly opts in with
`DEV_AUTH_MODE=true`. Single source of truth: `is_strict_auth()` in `app.py`.

Role vocabulary in V1: `student` (default), `admin` (custom claim or
server-side `users/{uid}.role`). **TEACHER / SUPER_ADMIN / institution scope do
not exist in V1** — marked N/A below (V1 hardening pass; not implemented).

Ownership rule key: SELF = caller acts only on own verified uid; ANY(public) =
no private data; ADMIN = verified admin.

| Endpoint | Method | Required auth | Required role | Ownership rule | Institution rule | Rate limit | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| `/health`, `/api/health` | GET | none (PUBLIC) | — | ANY | N/A — NOT PRESENT IN V1 | no | PASS | liveness only, no AI/secrets/paths |
| `/api/ready` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | engine + pool>=100, 503 when not ready |
| `/chat`, `/ask` | POST | none (PUBLIC) | — | ANY | N/A | YES (IP bucket) | PASS | safe errors, 3k msg cap |
| `/api/tutor/query` | POST | none (PUBLIC) | — | ANY (session-scoped) | N/A | no | PASS | strict int/range validation |
| `/api/tutor/step` | POST | none (PUBLIC) | — | ANY (session id) | N/A | no | PASS | step 1..4 enforced |
| `/api/tutor/verify` | POST | none (PUBLIC) | — | ANY (session id) | N/A | no | PASS | index 0..3 enforced |
| `/api/tutor/tracker` | GET | ADMIN | admin | ADMIN | N/A | no | PASS | anon → 401/403; limit 1..100 |
| `/api/tutor/dataset-info` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | corpus metadata only |
| `/api/tutor/import-kaggle` | POST | ADMIN | admin | ADMIN | N/A | no | PASS | anon → 401/403; errors clamped |
| `/api/mcq/generate` | POST | none (PUBLIC) | — | ANY (anonymous-safe) | N/A | no | PASS | read-only serving; identity header-preferred |
| `/api/mcq/submit` | POST | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | mismatch body id → 403; strict anon → 401 |
| `/api/mcq/submit-batch` | POST | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | same; attempts capped 100 |
| `/api/learner/profile` | GET | STUDENT | student | SELF unless admin | N/A | no | PASS | header-vs-query match enforced |
| `/api/learner/review-due` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | anonymous-safe empty in strict |
| `/api/syllabus` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | static |
| `/api/score/predict` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | inputs clamped 0..180 |
| `/api/score/history` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | — |
| `/api/coach/tip` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | never leaks retrieval errors |
| `/api/textbook/chapters` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | static index |
| `/api/textbook/pdf/<chapter_id>` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | map-lookup (traversal-safe), 404 JSON |
| `/api/flashcards` | POST | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | front/back required |
| `/api/flashcards/due` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | limit 1..100 |
| `/api/flashcards/review` | POST | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | card required |
| `/api/flashcards/stats` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | — |
| `/api/flashcards` (list) | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | — |
| `/api/mcqs/seed` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | static bank page, limit 1..200 |
| `/api/mcqs/generate` | POST | ADMIN | admin | ADMIN | N/A | no | PASS | anon → 401/403; count 1..50 |
| `/api/flashcards/<card_id>` | DELETE | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | — |
| `/api/flashcards/<card_id>` | PATCH | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | — |
| `/api/safety/metrics` | GET | none (PUBLIC) | — | ANY | N/A | no | PASS | aggregate counters |
| `/api/tutor/answer` | POST | none (PUBLIC) | — | ANY (anonymous-safe) | N/A | YES (IP bucket) | PASS | invalid credential → anonymous, never spoofed |
| `/api/chat/thread` | GET | STUDENT (read) | student | SELF (strict: token uid) | N/A | no | PASS | last 20 turns |
| `/api/chat/thread` | DELETE | STUDENT (write) | student | SELF via resolve_identity | N/A | no | PASS | — |
| `/api/tutor/answer/stream` | POST | none (PUBLIC) | — | ANY (anonymous-safe) | N/A | no | PASS | SSE meta/chunk/done |

TEACHER role endpoints: N/A — NOT PRESENT IN CURRENT V1.
SUPER_ADMIN role endpoints: N/A — NOT PRESENT IN CURRENT V1.
Institution scoping: N/A — NOT PRESENT IN CURRENT V1.
Global: MAX_CONTENT_LENGTH 256 KB; all errors user-safe (no traces/secrets);
rate limiter is process-local in-memory (documented; Redis = future work).
