# 🚀 BioNEETPro V3 — Production Deployment Guide

## 1. Architecture Overview
BioNEETPro V3 is designed for deployment across cloud platforms such as **Vercel** (Frontend & Static Edge) and **Render / Google Cloud Run** (Flask API & AI Intelligence Engine).

---

## 2. DNS & Subdomain Configuration

To enable the multi-portal experience under production domains, configure the following DNS records in your domain registrar (e.g. Cloudflare, Namecheap, GoDaddy):

| Type | Hostname / Subdomain | Target / Value | Purpose |
| :--- | :--- | :--- | :--- |
| **A / ALIAS** | `bioneetpro.com` | `76.76.21.21` (Vercel IP) or CNAME | Ecosystem Gateway (Landing) |
| **CNAME** | `students.bioneetpro.com`| `cname.vercel-dns.com` | Student Learning Portal |
| **CNAME** | `teachers.bioneetpro.com`| `cname.vercel-dns.com` | Teacher Assessment Studio |
| **CNAME** | `admin.bioneetpro.com` | `cname.vercel-dns.com` | Super Admin Governance Console |
| **CNAME** | `api.bioneetpro.com` | `bioneetpro.onrender.com` | Central Backend API Gateway |

> [!TIP]
> **Dual-Mode Compatibility:**
> Even before DNS records propagate or in preview environments, the application automatically handles path-based routing (`/student`, `/teacher`, `/admin`).

---

## 3. Vercel Configuration (`vercel.json`)

Ensure `vercel.json` contains rewrites that forward portal routes to `index.html` while proxying `/api/*` calls to the Python backend:

```json
{
  "version": 2,
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://bioneetpro.onrender.com/api/$1"
    },
    {
      "source": "/student/(.*)",
      "destination": "/index.html"
    },
    {
      "source": "/student",
      "destination": "/index.html"
    },
    {
      "source": "/teacher/(.*)",
      "destination": "/index.html"
    },
    {
      "source": "/teacher",
      "destination": "/index.html"
    },
    {
      "source": "/admin/(.*)",
      "destination": "/index.html"
    },
    {
      "source": "/admin",
      "destination": "/index.html"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" }
      ]
    }
  ]
}
```

---

## 4. Production Environment Variables Checklist

Set the following environment variables in your Render / Cloud Run dashboard:

| Variable Name | Recommended Value (Production) | Description |
| :--- | :--- | :--- |
| `REQUIRE_FIREBASE_AUTH` | `true` | Enforces fail-closed token validation on all protected endpoints. |
| `DEV_AUTH_MODE` | `false` | Disables mock/dev role headers in production. |
| `FIREBASE_PROJECT_ID` | `bioneet-pro` | Your production Firebase project identifier. |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | API key for Dr. Priya and Prof. Sharma AI generation. |
| `OPENROUTER_MODEL` | `gpt-4o-mini` | Recommended high-speed, cost-effective biology LLM. |
| `ALLOWED_ORIGINS` | `https://bioneetpro.com,https://students.bioneetpro.com,https://teachers.bioneetpro.com,https://admin.bioneetpro.com` | Allowed CORS origins. |
| `PORT` | `5000` | Port for the Gunicorn / Flask server. |

---

## 5. Backend Start Command

For Render / containerized deployment:

```bash
gunicorn --workers 4 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

---

## 6. Pre-Flight Deployment Verification
Before promoting to production, execute the verification suite:
```bash
# 1. Run all unit tests (121 tests)
python -m unittest discover -s tests

# 2. Run the 30-point mission-critical verification
python tests/verify_30_points.py

# 3. Verify HTML byte-for-byte SHA-256 parity
powershell -Command "Get-FileHash index.html, BioNeet-Pro.html"
```
Both files MUST share the identical SHA-256 hash before git commit and push.
