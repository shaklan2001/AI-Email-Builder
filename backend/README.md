# Backend — AI Email Workflow Builder

Python API managed with **[uv](https://docs.astral.sh/uv/)**.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed

## Setup

```bash
cd backend
uv sync
cp .env.example .env   # optional — health check works without it
```

## Verify setup

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health — expect `{"status":"ok","service":"email-workflow-builder-api"}`.

## Commands

| Task | Command |
|---|---|
| Install deps | `uv sync` |
| Add package | `uv add <package>` |
| Run API | `uv run uvicorn app.main:app --reload` |
| Lint | `uv run ruff check app` |

Do not use `pip install` — use `uv add` only.

## Layout

`app/` mirrors the LLD folder structure. Packages are empty placeholders until feature work begins.
