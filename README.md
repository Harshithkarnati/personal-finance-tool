# Personal Finance Tool

Minimal full-stack expense tracker built with Django and React.

## Stack

- Backend: Django with SQLite persistence
- Frontend: React with Vite
- API: `POST /expenses` and `GET /expenses`

## Why SQLite

SQLite keeps the app easy to run locally while still behaving like a real database. It gives us durable storage across reloads without introducing extra infrastructure for this exercise.

## Key Design Decisions

- The backend stores expenses as proper decimal amounts so money is not handled with floating point math.
- POST requests are retry-safe through an idempotency record. The frontend also keeps a pending submission key in local storage so repeated clicks and page reloads do not create duplicate expenses.
- The frontend requests filtered data from the API and performs the final visible sort locally so the UI stays simple.
- The UI shows loading and error states so slower or failed responses are still understandable.

## Trade-offs

- If the client does not provide a stable idempotency key, the backend falls back to a deterministic fingerprint of the request body. That makes retries safe, but it also means two intentionally identical expense submissions are treated as the same request.
- Category filtering is exact and case-insensitive rather than supporting advanced search.
- The app keeps the feature set intentionally small instead of adding authentication, edit/delete flows, or category summaries.

## Intentionally Not Done

- No user accounts or multi-user authorization
- No edit or delete endpoints
- No separate analytics dashboard
- No production deployment setup

## Run It

Backend:

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/expenses` to `http://127.0.0.1:8000`, so the UI can talk to the Django API without extra CORS setup.

## Tests

```bash
cd backend
python manage.py test
```