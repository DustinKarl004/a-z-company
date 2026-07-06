# Z.A. Company — Frontend

Vue 3 + Vite frontend. This slice covers login and the admin's Branches/Staff management screens, matching what the backend currently supports (see `../backend/README.md`). Staff who log in see a placeholder — stock/sales entry isn't built on the backend yet.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your running backend if not the default
```

## Run the dev server

Make sure the backend is running first (see `../backend/README.md`), then:

```bash
npm run dev
```

Open the printed local URL, log in with the seeded admin credentials.

## Build

```bash
npm run build
```

## Notes

- State: one Pinia store (`src/stores/auth.js`) holds the JWT and persists it to `localStorage`. `role`/`branch_id` are decoded client-side from the JWT payload for routing/display only — the backend enforces real authorization.
- API calls go through `src/api/client.js`, a thin `fetch` wrapper that attaches the bearer token and redirects to `/login` on a 401.
- No component library — plain scoped CSS using the palette defined in `src/styles/variables.css` (matches the hex values in the top-level README).

## Deploying to Vercel

1. Import this repo into Vercel and set the project's **root directory to `frontend/`** (it's a monorepo). Vercel auto-detects Vite — no extra build config needed.
2. Set the env var `VITE_API_BASE_URL` in the Vercel project settings to your deployed Railway backend URL (e.g. `https://za-company-backend.up.railway.app`). It's baked in at build time, so redeploy after changing it.
3. `vercel.json` in this folder rewrites all routes to `index.html` — needed because `vue-router` uses browser history mode, so a direct refresh on e.g. `/admin/branches` would otherwise 404.
4. On the backend, set `CORS_ORIGINS` to this Vercel URL once it exists (see `../backend/README.md`) so the browser isn't blocked by CORS.
