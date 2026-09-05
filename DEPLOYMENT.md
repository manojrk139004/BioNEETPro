# DEPLOYMENT.md — BioNEETPro V1 Deploy Guide (release freeze)

## Backend (container)
```bash
docker build -t bioneetpro-v1 .
docker run -d --name bioneetpro -p 5000:5000 \
  -e ALLOWED_ORIGINS=https://YOUR-FRONTEND-DOMAIN \
  -e FIREBASE_SERVICE_ACCOUNT_JSON='<service-account-json>' \
  -e OPENROUTER_API_KEY='<key>' \
  bioneetpro-v1
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/ready
```
- Image runs gunicorn (2 workers, 120 s timeout). Do NOT use `python app.py`
  in production (dev server only).
- Production env: leave `REQUIRE_FIREBASE_AUTH` unset (strict) and DO NOT set
  `DEV_AUTH_MODE`. Provide Firestore credentials (required for writes).
- Status on audit machine: DOCKER RUNTIME VERIFICATION = NOT VERIFIED
  (no Docker daemon). Dockerfile statically verified (all modules + data,
  gunicorn CMD, no secrets baked in). Run the commands above on the deploy
  host and confirm `/api/health` + `/api/ready` before routing traffic.

## Frontend (static)
Deploy `BioNeet-Pro.html` to any static host. Set
`window.BIONEET_AI_BACKEND_URL = "https://YOUR-BACKEND"` before the main
script when frontend and backend are split across hosts; same-origin is the
fallback on deployed domains; localhost auto-maps to `:5000` for dev.

## Firebase
```bash
firebase deploy --only firestore:rules,firestore:indexes
```
- Admin bootstrap (one time, console): register the admin user in-app, then set
  its `users/{uid}.role` to `"admin"`.
- `Textbook/` PDFs (35 files) must be present beside the backend for
  `/api/textbook/pdf/*`; they are intentionally excluded from the audit ZIP.

## Health
- `GET /health` and `GET /api/health`: liveness (no AI, no secrets).
- `GET /api/ready`: readiness (engine + MCQ pool loaded; 503 otherwise).

## Scaling notes
- Single-instance: current in-memory rate limiting is sufficient.
- Multi-instance: add shared Redis rate limiting (documented future work).
- Vercel serverless NOT recommended for the backend (bundle size, timeouts,
  ephemeral FS) — see DEPLOYMENT_NOTES.md.
