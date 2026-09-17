# Pantone Extractor Web App

Next.js + Vercel Python Runtime app for extracting PDF colors and returning separate PNG, PDF, and CSV downloads. The Python function creates files in a temporary directory, encodes them into browser downloads, and the UI clears the links after 30 minutes—no paid storage required.

## Local

```bash
npm install
copy .env.example .env.local
npm run dev
```

Install Python dependencies with `pip install -r requirements.txt`. Default login is `demo@pantone.local` / `change-me-now`; set `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and a long random `SESSION_SECRET` before deployment.

## Deploy for $0

Push this folder to GitHub, import it into Vercel Hobby, and add the three environment variables. Vercel detects `api/extract.py` automatically. Keep PDFs under 25 MB and processing under the Hobby function limit. This is intentionally a single-user internal tool: there is no user database, registration flow, or Supabase dependency.
