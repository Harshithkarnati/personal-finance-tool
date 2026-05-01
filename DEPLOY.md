Deployment steps — Backend (Render) and Frontend (Vercel)

Overview
- Backend: Django app in `backend/` will be deployed on Render (or any other host providing Postgres and web services).
- Frontend: Vite + React app in `frontend/` will be deployed to Vercel and will talk to the backend via `VITE_API_URL`.

Backend (Render)
1. Commit and push your repo to GitHub (or connect your repo to Render).
2. In Render, create a new "Web Service" and connect the repository (either the monorepo root or the `backend/` folder):
   - Build Command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn expense_tracker.wsgi:application --bind 0.0.0.0:$PORT`
   - Environment: set the following env vars on the Render service:
     - `SECRET_KEY` — a long, random secret
     - `DATABASE_URL` — Postgres connection string (use Render Postgres addon or external managed Postgres)
     - `DEBUG=false`
     - `ALLOWED_HOSTS` — comma-separated hosts (e.g., `your-backend.onrender.com`)
     - `CSRF_TRUSTED_ORIGINS` — comma-separated frontend origin(s): `https://your-frontend.vercel.app`
     - `CORS_ALLOWED_ORIGINS` — same as above or set `CORS_ALLOW_ALL_ORIGINS=true` for quick testing
     - Optionally: `SESSION_COOKIE_SECURE=true`, `CSRF_COOKIE_SECURE=true`, `SECURE_SSL_REDIRECT=true`
3. If using Render managed Postgres, add the database and copy `DATABASE_URL` into the service env.
4. Deploy — Render will run the build command and start gunicorn. Verify logs for `migrate` and `collectstatic` success.

Frontend (Vercel)
1. In the frontend source, API calls now read `import.meta.env.VITE_API_URL`. On Vercel you must set this env var.
2. Push the repo to GitHub (if not already). Create a new Vercel project and import the repo.
3. In Vercel Project Settings → Environment Variables, add:
   - `VITE_API_URL` = `https://<your-backend-host>` (e.g., `https://your-backend.onrender.com`)
4. Build Settings on Vercel:
   - Framework Preset: Vite (or manually set)
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Deploy. Vercel will build the static site and publish it.

DNS / HTTPS
- Both Render and Vercel provide HTTPS automatically for their domains. If you add custom domains, follow the provider docs to add DNS records.

Local testing
- Backend local run (for dev):
```powershell
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
- Frontend local run (for dev):
```bash
cd frontend
npm install
npm run dev
```
- If testing frontend against local backend, set `VITE_API_URL=http://localhost:8000` in a `.env` file in `frontend/` (Vite reads `.env` by default):
```
# frontend/.env
VITE_API_URL=http://localhost:8000
```

Troubleshooting
- CSRF 403 on POSTs: ensure `CSRF_TRUSTED_ORIGINS` contains the frontend origin and that requests include CSRF tokens if using session auth. Consider using token-based auth (JWT) for API-only setups.
- 500 on static files: ensure `collectstatic` succeeded and `STATIC_ROOT` exists.
- DB connection errors: verify `DATABASE_URL` formatting and that the Postgres firewall allows Render to connect.

Extra: Deploy checklist (quick)
- [ ] Add production env vars on Render and Vercel
- [ ] Ensure `requirements.txt` includes `gunicorn`, `whitenoise`, `dj-database-url`, `django-cors-headers`, and Postgres driver
- [ ] Confirm `Procfile` exists (optional) and start command configured
- [ ] Confirm `VITE_API_URL` points to backend

If you want, I can:
- Create a small `.env.example` for both `backend/` and `frontend/`.
- Run a local sanity check (install backend deps and run `migrate`/`collectstatic`) and report any errors.
