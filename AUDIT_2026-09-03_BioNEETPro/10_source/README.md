# BioNEET Pro

NEET Biology preparation platform: **single-file frontend + Flask AI backend**.

## The app (source of truth)

- **`BioNeet-Pro.html`** — the main project. Open it with VS Code **Live Server**
  (right-click the file → *Open with Live Server*, usually port 5500).
  DNA-helix hero, Dashboard, Mock Test, AI Tutor, Flashcards, Lessons, Videos,
  Updates, Leaderboard. Talks to the backend at `http://127.0.0.1:5000`.
- **`app.py`** — Flask backend (AI tutor, MCQ engine, learner profiles).
  Run it first: `python app.py` (or `npm` is NOT needed for anything anymore).

## Run order (both must run)

```bash
python app.py
# then: right-click BioNeet-Pro.html -> Open with Live Server
```

## Backend env (.env.local, git-ignored)

- `OPENROUTER_API_KEY` (server only — never commit a real key)
- `ALLOWED_ORIGINS` (must include your Live Server origin)
- `PORT` (default 5000)

## AI tutor endpoints

- `POST /api/tutor/answer` — unified single-brain answer (chat + step modes)
- `POST /api/tutor/answer/stream` — SSE streaming variant
- `POST /chat`, `POST /ask` — legacy chat paths (kept working)
- `POST /api/tutor/query|step|verify`, `GET /api/tutor/tracker`
- `POST /api/mcq/generate|submit`, `GET /api/learner/profile|review-due`, `GET /api/syllabus`

## Verify

```bash
python evaluate_tutor_beast.py   # golden tutor set, must be all PASS
```

## Notes

- `Textbook/` holds the 32 rationalized NCERT Biology PDFs (19 Class XI + 13 Class XII);
  `data/ncert_textbook_index.json` is the parsed chunk index (774 chunks).
- `css/` and `js/` are unused leftovers from an older version (safe to archive).
- Never commit `.env.local` or real API keys.
