# Spoti-Insights

A full-stack Spotify analytics dashboard. It authenticates with your Spotify
account, continuously syncs your listening history into a database, and surfaces
insights you can't get from Spotify directly — listening trends over time, genre
distribution, hourly activity patterns, and your top artists and tracks by
real play count.

<!-- SCREENSHOT 1: Hero / Dashboard                            -->

> **Live demo:** [spoti-insights-app](https://spoti-insights-app.onrender.com/)

> _Note: the live demo uses cross-domain cookies; if login fails in
> incognito/Safari, that's third-party-cookie blocking — see
> [Auth & Cookies](#auth--cookies)._

---

## Why this exists

Spotify's own app shows you "Wrapped" once a year and a fixed "recently played"
list capped at 50 tracks. Spoti-Insights runs a background job that captures
every play into a persistent database, so it can compute analytics over
arbitrary time windows that Spotify's API alone can't provide — your real
top tracks by play count, daily listening trends, when in the day you listen
most, and how your taste breaks down by genre.

---

## Features

- **OAuth2 authentication with Spotify** — full authorization-code flow, with
  JWT access/refresh tokens stored in httpOnly cookies.
- **Token rotation & denylisting** — refresh tokens are single-use; consumed
  tokens are denylisted in Redis so they can't be replayed.
- **Background listening-history sync** — a scheduled job pulls recently-played
  tracks every 15 minutes and upserts them into Postgres, building a long-term
  history beyond Spotify's 50-track limit.
- **Derived analytics** (computed from your own data, not just proxied):
  - Listening trends — daily plays/minutes over a configurable window
  - Genre distribution — aggregated from your top artists' genre tags
  - Hourly velocity — when during the day you listen most
  - Top artists & tracks by real play count
  - Today's activity summary
- **Playlists & history browsing** — paginated library view and an
  infinite-scroll listening history feed with relative timestamps.
- **Redis-backed caching & rate limiting** — Spotify tokens cached with TTL;
  endpoints rate-limited to prevent abuse.
- **Responsive UI** — works on mobile (collapsible sidebar) through desktop.

---

## App preview

### Dashboard
<img width="1365" height="632" alt="Screenshot 2026-06-26 175303" src="https://github.com/user-attachments/assets/e56f5c1b-8fa3-40eb-9458-4fe61a9f4753" />


### Listening History (infinite scroll, relative timestamps)
<img width="1351" height="628" alt="image" src="https://github.com/user-attachments/assets/b3c3d5aa-db0b-48bb-a2cb-fa504b622304" />

<!-- ### Playlists -->
<!-- ![Playlists](docs/screenshots/playlists.png) -->

<!-- ### Genre Distribution & Listening Trends (close-up of the charts) -->
<!-- ![Charts](docs/screenshots/charts.png) -->

<!-- ### Mobile view (show the responsive layout / collapsible sidebar) -->
<!-- ![Mobile](docs/screenshots/mobile.png) -->

---

## Tech Stack

**Frontend**
- React + TypeScript
- Vite
- Tailwind CSS
- TanStack Query (React Query) for server state
- React Router
- Custom SVG data visualizations (no charting library — line chart, donut, and
  histograms are hand-rolled SVG)

**Backend**
- FastAPI (Python 3.12)
- PostgreSQL + SQLAlchemy
- Alembic (migrations)
- Redis (token cache, rate limiting, refresh-token denylist)
- APScheduler (background sync job)
- httpx (async Spotify API client)

**Infrastructure**
- Deployed on Render (static site + web service + managed Postgres/Redis)

---

## Architecture

```
┌─────────────┐      OAuth2 / API calls       ┌──────────────┐
│   React     │ ───────────────────────────▶  │   FastAPI    │
│  (Vite SPA) │ ◀───────────────────────────  │   backend    │
└─────────────┘      httpOnly JWT cookies      └──────┬───────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────┐
                          ▼                           ▼                       ▼
                   ┌────────────┐            ┌────────────┐          ┌────────────────┐
                   │ PostgreSQL │            │   Redis    │          │  Spotify API   │
                   │ (history,  │            │ (token     │          │ (OAuth, top    │
                   │  users)    │            │  cache,    │          │  items, etc.)  │
                   └────────────┘            │  denylist, │          └────────────────┘
                          ▲                  │  ratelimit)│
                          │                  └────────────┘
                   ┌──────┴───────┐
                   │ APScheduler  │  every 15 min: pull recently-played,
                   │ sync job     │  upsert into listening_history
                   └──────────────┘
```


**Data flow in brief:** the user authenticates via Spotify OAuth2; the backend
stores JWTs in httpOnly cookies. A scheduled job continuously syncs the user's
plays into Postgres. Analytics endpoints aggregate that stored history (fast,
no Spotify round-trip), while live data (top items, playlists) is fetched from
Spotify on demand and cached in Redis.

---

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.12+
- PostgreSQL and Redis (or Docker — see [Docker](#run-with-docker))
- A Spotify Developer application
  ([dashboard](https://developer.spotify.com/dashboard))

### 1. Spotify app setup
Create an app in the Spotify Developer Dashboard and add a redirect URI:
```
http://127.0.0.1:8000/public/auth/spotify/callback
```
Note your **Client ID** and **Client Secret**.

### 2. Environment variables
Create a `.env` in the repo root:

```env
# App
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://127.0.0.1:5173

# Spotify
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/public/auth/spotify/callback

# Database & Redis
DATABASE_URL=postgresql+psycopg://postgres:1234@localhost:5432/spoti_insights
REDIS_URL=redis://localhost:6379/0
```

Create `frontend/.env.local`:
```env
VITE_API_URL=http://127.0.0.1:8000
```

### 3. Backend
```bash
# from repo root
uv sync                       # or: pip install -r requirements.txt
alembic upgrade head          # run migrations
uv run uvicorn backend.main:app --reload
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

App runs at `http://127.0.0.1:5173`, backend at `http://127.0.0.1:8000`
(API docs at `/api/docs`).

---

## Auth & Cookies

Auth tokens are stored in **httpOnly cookies** (not localStorage) so they can't
be read by JavaScript — this protects them from XSS.

Because the deployed frontend and backend live on different domains, cookies
are configured as `SameSite=None; Secure` in production and `SameSite=Lax`
locally, derived automatically from the `ENVIRONMENT` variable. The cross-domain
production setup relies on third-party cookies, which incognito mode and Safari
block by default — the permanent fix is hosting both under a shared parent
domain (`app.example.com` + `api.example.com`). <!-- See
[deployment notes](docs/deployment-cookie-notes.md) for the full reasoning. -->

---

## Project Structure

```
.
├── backend/
│   ├── routers/          # API endpoints (auth, analytics, deep_analytics, ...)
│   ├── services/         # Spotify client, auth, token logic
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── jobs/             # APScheduler sync job
│   ├── core/             # config, dependencies, rate limiter
│   └── main.py
├── frontend/
│   └── src/
│       ├── api/          # axios client + API functions
│       ├── components/   # dashboard, layout, ui components
│       ├── hooks/        # React Query hooks
│       └── pages/
├── alembic/              # database migrations
└── docker-compose.yml    # local dev stack
```

---

## Roadmap

Tracked in [Issues](../../issues). Highlights:
- Route guards to prevent re-authentication when already logged in
- Silent token refresh on login when a valid session exists
- Expanded test coverage

---

## License

MIT

---

## Acknowledgements

Built as a full-stack portfolio project. Spotify data accessed via the
[Spotify Web API](https://developer.spotify.com/documentation/web-api).
This project is not affiliated with or endorsed by Spotify.
