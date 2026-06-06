# AI Email Workflow Builder

Full-stack app for building and running AI-powered email workflows.

| Layer | Stack |
|---|---|
| Frontend | React 19, Vite, MUI, TanStack Query |
| Backend | FastAPI, MongoDB, Celery, LangGraph |
| Queue | Redis (Celery broker) |

## Prerequisites

- **Node.js** 20+
- **Python** 3.12+
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** (Python package manager)
- **Redis** (local install or Docker)
- **MongoDB** (Atlas or local)

---

## 1. Redis

Redis must be running before you start the backend worker.

### macOS (Homebrew)

```bash
brew install redis
brew services start redis
```

### Docker

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Verify Redis is up:

```bash
redis-cli ping
# Expected: PONG
```

Default connection: `redis://localhost:6379`

---

## 2. Backend

```bash
cd backend
uv sync
cp .env.example .env   # fill in MongoDB, Clerk, Groq, Resend keys
```

### API server

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/health

### Celery worker (required for workflow execution)

Run in a **separate terminal** (with Redis running):

```bash
cd backend
uv run celery -A app.workers.celery_app worker -l info -Q workflow_queue,email_queue,retry_queue
```

---

## 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set VITE_API_URL and Clerk key if needed
npm run dev
```

Open http://localhost:5173

---

## Quick start (all services)

Use **four terminals**:

| Terminal | Command |
|---|---|
| 1 — Redis | `brew services start redis` (or Docker command above) |
| 2 — API | `cd backend && uv run uvicorn app.main:app --reload --port 8000` |
| 3 — Worker | `cd backend && uv run celery -A app.workers.celery_app worker -l info -Q workflow_queue,email_queue,retry_queue` |
| 4 — UI | `cd frontend && npm install && npm run dev` |

---

## Environment variables

| Location | File | Purpose |
|---|---|---|
| Backend | `backend/.env` | MongoDB, Redis, Clerk, Groq, Resend, LangSmith |
| Frontend | `frontend/.env.local` | `VITE_API_URL`, `VITE_CLERK_PUBLISHABLE_KEY` |

See `.env.example` in each folder for the full list. **Never commit `.env` files.**

---

## Other commands

```bash
# Backend lint
cd backend && uv run ruff check app

# Backend tests
cd backend && uv run pytest

# Frontend production build
cd frontend && npm run build
```

---

## Project layout

```
├── backend/     # FastAPI API + Celery workers + LangGraph agents
├── frontend/    # React UI
├── docs/        # Design docs
└── context/     # Feature specs and progress tracker
```

More detail: `backend/README.md`, `frontend/README.md`, `ARCHITECTURE_DECISIONS.md`.
