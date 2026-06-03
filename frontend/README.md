# Frontend — AI Email Workflow Builder

React 19 + Vite + **MUI** + **TanStack Query** + Clerk (optional until keys are set).

## Prerequisites

- Node.js 20+

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

## Verify setup

```bash
npm run dev
```

Open http://localhost:5173 — you should see **Frontend setup OK**.

```bash
npm run build
```

Build should complete without errors.

## Environment

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Backend base URL (default proxied to `:8000`) |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk auth (optional for setup check) |

## Layout

`src/` mirrors the LLD structure. Pages and API hooks are placeholders until feature work begins.
