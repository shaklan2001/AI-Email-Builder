# Progress Tracker

Update after every meaningful implementation change.

## Current Phase

**Resend email delivery (immediate send)** — backend can send the first `send_email` step’s `final_user_version` content via Resend. Provider abstraction in place; no workflow scheduling or webhooks in this slice.

## Current Goal

Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` in `backend/.env`; ensure workflow `workflow_definition` in MongoDB includes `recipient_emails` (or `recipients` with `email` fields) for the workflow under test; call `POST /api/v1/email/send` with `{ "workflowId": "..." }` and confirm Resend delivery. Wire frontend send/activate UI when requested.

## Completed

- PRD, HLD, LLD, sequence diagrams in `docs/`
- Pre-code artifacts: screen flow, LangGraph stages, MongoDB indexes, MVP scope
- ADR-001–011 in `ARCHITECTURE_DECISIONS.md`
- Agent entry: `Agent.md` + `context/` (6 files)
- `frontend/` — Vite, React 19, MUI, TanStack Query (`npm install`, build OK)
- `backend/` — FastAPI scaffold, LLD folder tree, `uv sync` + `uv.lock`
- **Authentication (feature spec `01-authentication.md`):**
  - `ClerkProvider` in `frontend/src/main.tsx`
  - `/sign-in`, `/sign-up` with Clerk `<SignIn />` / `<SignUp />`
  - Client route guards: public (`PublicRoute`), protected (`ProtectedRoute`)
  - Root `/` → `/dashboard` (signed in) or `/sign-in` (signed out)
  - Protected: `/dashboard`, `/workflows/*`
  - `UserButton` in `AppNavbar` on protected layout
- **Dashboard (feature spec `02-dashboard.md`):**
  - `/dashboard` — page header, Create Workflow button, workflow list section
  - `WorkflowCard` — name, status chip, created date
  - `DashboardEmptyState` — icon, description, Create Workflow CTA
  - Mock data in `frontend/src/mocks/workflows.ts` (no backend)
  - Responsive `Container` + `Grid2` layout
  - `@mui/icons-material` added (v6, matches MUI)
- **Builder layout (feature spec `03-builder-layout.md`):**
  - `/workflows/:workflowId` — `WorkflowBuilderPage` with `BuilderLayout`
  - Left panel: chat area shell (fully implemented in spec 05)
  - Right panel: `PreviewPanel` — workflow preview only (spec 06)
  - Split layout ~40% / ~60%, full viewport below navbar; stacks vertically on `xs`/`sm`
  - Removed `WorkflowsPlaceholderPage` (replaced by builder route)
- **Chat panel (feature spec `05-chat-panel.md`):**
  - `frontend/src/components/chat/chat-panel.tsx` — header, message list, fixed input
  - `message-list.tsx`, `user-message.tsx`, `assistant-message.tsx`, `chat-input.tsx`
  - `frontend/src/mocks/chat-messages.ts` — initial mock + static mock assistant reply on send
  - Local state only; no API calls
  - Auto-scroll on new messages; Enter to send (Shift+Enter for newline)
  - `BuilderLayout` imports `ChatPanel` from `components/chat/`
- **Builder experience (feature spec `06-builder-experience.md`):**
  - `ai-prompt-screen.tsx` — centered Lovable-style prompt UI (heading, description, large input, CTA)
  - `WorkflowBuilderPage` — Stage 1 prompt → fade transition → Stage 2 builder (no route change, no reload)
  - First prompt stored locally; initial user message + empty assistant placeholder in chat
  - `workflow-preview-placeholder.tsx` — mock branching workflow diagram
  - `PreviewPanel` — Email and Recipients tabs removed; workflow preview only
  - `CreateWorkflowButton` — navigates to `/workflows/new`
  - No backend, AI, or LangGraph calls
- **Workflow state sync (feature spec `07-workflow-state-sync.md`):**
  - `BuilderLayout` — shared `messages` state; `workflow` derived with `deriveWorkflowFromChat`
  - `lib/derive-workflow-from-chat.ts` — keyword detection from all user messages (chat = source of truth)
  - `wait N days` → updates wait step label; `follow up` → adds Follow Up Email node; `discount` → adds Discount Email node
  - `types/workflow-state.ts` — local workflow model + default (matches prior placeholder diagram)
  - `workflow-preview.tsx` — renders from `WorkflowState` props (replaces static placeholder)
  - `ChatPanel` — controlled messages via `messages` + `onMessagesChange`
  - React state only; no API calls
- **Recipient management (feature spec `08-recipient-management.md`):**
  - `components/recipients/recipient-management.tsx` — footer bar with CSV Upload + Manual Entry buttons
  - `csv-upload-dialog.tsx` — CSV file picker, parses email column, validates rows
  - `manual-entry-dialog.tsx` — single email input with validation
  - `recipient-summary.tsx` — Valid Count + Invalid Count chips
  - `lib/validate-recipient-email.ts` — required email + format validation, CSV parsing
  - `types/recipient.ts` — Recipient, InvalidRecipient, RecipientCounts types
  - `mocks/recipient-storage.ts` — in-memory Map keyed by workflowId (valid recipients stored; invalid count tracked)
  - `BuilderLayout` — recipient footer below chat/preview split; accepts `workflowId` prop
  - No backend integration
- **Workflow review (feature spec `09-workflow-review.md`):**
  - `/workflows/:workflowId/review` — `WorkflowReviewPage` with `WorkflowReview` component
  - `components/review/workflow-review.tsx` — all five sections + Approve Workflow button
  - `types/workflow-review.ts` — review data model
  - `mocks/workflow-review.ts` — mock review data via `getMockWorkflowReview`
  - No backend integration
- **Workflow persistence (feature spec `10-workflow-persistence.md`):**
  - `lib/workflow-persistence.ts` — load/save/clear drafts in `localStorage`; schema validation; corrupt draft removal
  - `types/workflow-draft.ts` — draft model (workflow, messages, campaign metadata, recipients)
  - `components/builder/draft-status-bar.tsx` — “Saving draft…” / “Draft saved” chip + Clear Draft button
  - `BuilderLayout` — debounced auto-save on state changes; hydrates recipients into mock storage on restore path via page boot
  - `WorkflowBuilderPage` — detects draft on load; restores prompt vs builder stage, chat, campaign `firstPrompt`
  - `mocks/recipient-storage.ts` — `setStoredRecipients` for draft restore
  - Browser storage only; no backend
- **Backend API foundation (feature spec `11-backend-api-foundation.md`):**
  - `app/core/config.py` — pydantic-settings from env (`CORS_ORIGINS`, `CLERK_PEM_PUBLIC_KEY`, etc.)
  - `app/core/logger.py` — structlog setup
  - `app/core/security.py` — Clerk JWT validation via `get_current_user` dependency (RS256 + PEM key)
  - `app/core/exception_handlers.py` — consistent `ErrorResponse` for validation, HTTP, and unhandled errors
  - `app/schemas/responses.py` — `SuccessResponse`, `ErrorResponse`, `ErrorDetail`
  - `app/schemas/requests.py` — request/response data models per endpoint
  - `app/api/chat.py` — `POST /api/v1/chat/message` (mock assistant reply)
  - `app/api/workflows.py` — `POST /api/v1/workflows`, `GET /api/v1/workflows/{id}` (mock data)
  - `app/api/recipients.py` — `POST /api/v1/recipients/upload` (mock counts)
  - `app/api/review.py` — `POST /api/v1/review` (mock review data)
  - `app/main.py` — app factory, CORS, router registration, `GET /health` → `{"status":"ok"}`
  - No database, LangGraph, or email provider calls
- **Chat API integration (feature spec `12-chat-api-integration.md`):**
  - `frontend/src/services/chat.service.ts` — `sendMessage()` → `POST /api/v1/chat/message` with `{ message, workflowId }`
  - `frontend/src/hooks/use-send-chat-message.ts` — TanStack Query mutation
  - `frontend/src/components/chat/chat-panel.tsx` — API-backed send; loading, error, and retry UI; no local mock assistant reply
  - `frontend/src/api/client.ts` — `setAuthTokenGetter` + Bearer token on requests
  - `frontend/src/components/ApiAuthSetup.tsx` — Clerk `getToken` wired in protected layout
  - `backend/app/api/chat.py` — mock reply: `"Tell me more about your target audience."`
  - `backend/app/schemas/requests.py` — `ChatMessageRequest` (`message`, `workflowId`); `ChatMessageData` (`message`)
  - No LangGraph, Groq, LLM, or database persistence
- **Groq LLM integration (feature spec `14-groq-llm-integration.md`):**
  - `app/providers/llm/base.py` — `LLMProvider` ABC (`generate`, `extract_campaign_data`)
  - `app/providers/llm/groq_provider.py` — `GroqProvider` via official Groq SDK; JSON extraction with malformed-response fallback
  - `app/schemas/campaign.py` — Pydantic `CampaignData` (`business_goal`, `product_info`, `audience`, `tone`, `cta`)
  - `app/core/config.py` — `GROQ_API_KEY`, `GROQ_MODEL` (default `openai/gpt-oss-120b`)
  - `app/langgraph/state.py`, `nodes.py`, `graph.py` — extract + question nodes; strategist prompts
  - `app/services/chat_service.py` + `conversation_store.py` — in-memory session state per user/workflow
  - `app/api/chat.py` — routes messages through LangGraph + Groq (no mock reply)
  - `backend/.env.example` — `GROQ_MODEL` documented
  - No database persistence; no hardcoded campaign questions
- **Workflow generation agent (feature spec `15-workflow-generation-agent.md`):**
  - `app/agents/workflow_agent.py` — LLM-driven workflow structure (linear, conditional, multi-level conditional)
  - `app/schemas/workflow.py` — Pydantic `WorkflowDefinition` / `WorkflowStep`
  - `app/schemas/campaign.py` — `has_required_for_workflow()` (goal, product, audience, CTA)
  - `app/langgraph/nodes.py` — `generate_workflow_node`, `missing_information_node`, `route_after_missing_information`
  - `app/langgraph/graph.py` — extract → missing_information → question or generate workflow
  - `app/langgraph/state.py` — `workflow` field on `CampaignState`
  - `app/services/chat_service.py` — returns `ChatProcessResult` with optional workflow
  - `app/schemas/requests.py` — `WorkflowDefinitionData`, `WorkflowStepData` on chat response
  - `app/api/chat.py` — exposes workflow in `POST /api/v1/chat/message` response
  - `frontend/src/types/workflow-definition.ts` — API workflow types
  - `frontend/src/components/builder/workflow-preview.tsx` — renders steps from API JSON
  - `frontend/src/components/chat/chat-panel.tsx` — `onWorkflowChange` from API
  - `frontend/src/components/builder/BuilderLayout.tsx` — API workflow state for preview
  - No email content generation; no hardcoded workflow templates
- **Email generation agent (feature spec `16-email-generation-agent.md`):**
  - `app/agents/copywriter_agent.py` — subject, HTML, and plain text per `send_email` step (sales-focused, campaign-aware)
  - `app/schemas/email.py` — `GeneratedEmailContent` model
  - `app/schemas/workflow.py` — optional `email` on `WorkflowStep`
  - `app/langgraph/nodes.py` — `generate_emails_node` after `generate_workflow`
  - `app/langgraph/graph.py` — `generate_workflow` → `generate_emails` → END
  - `app/schemas/requests.py` — `GeneratedEmailData`, email on `WorkflowStepData`
  - `app/services/chat_service.py` — maps email fields from workflow state to API response
  - `frontend/src/types/workflow-definition.ts` — `GeneratedEmail` on steps
  - `frontend/src/services/chat.service.ts` — parses email from chat API workflow
  - `frontend/src/components/builder/workflow-preview.tsx` — subject + plain-text preview on send steps
  - No email sending
- **Human review loop (feature spec `17-human-review-loop.md`):**
  - `app/schemas/email.py` — `EmailBodyVersion`, `GeneratedEmailContent` with `ai_generated_version`, `final_user_version`, `user_edited`
  - `app/agents/copywriter_agent.py` — skips steps that already have AI or user-edited email content
  - `app/langgraph/nodes.py` — `route_after_missing_information` skips workflow regeneration when workflow already exists
  - `PATCH /api/v1/workflows/{workflowId}/emails/{stepId}` — persist user edits to conversation store
  - `app/services/workflow_email_service.py` — update `final_user_version` without touching AI draft
  - `frontend/src/components/builder/email-review-panel.tsx` — subject, HTML, plain text editing per send step
  - `frontend/src/services/workflow-email.service.ts` — PATCH client
  - `frontend/src/lib/email-content.ts` — `getFinalEmailContent`, `normalizeGeneratedEmail`, `updateWorkflowStepEmail`
  - `PreviewPanel` — Email Review section below workflow preview
  - Draft persistence includes `workflowDefinition` for edited emails across reloads
  - No automatic AI regeneration after user edits
- **MongoDB persistence (feature spec `18-mongodb-persistence.md`):**
  - `app/core/database.py`, `WorkflowRepository`, `ConversationRepository`, `persistence.py`
  - Chat and email PATCH persist campaign/workflow state to MongoDB
- **Resend email (feature spec `19-resend-email.md`):**
  - `app/providers/email/base.py` — `EmailProvider` ABC, `send_email()`, `EmailProviderError`
  - `app/providers/email/resend_provider.py` — `ResendProvider` via Resend SDK (`send_async`)
  - `app/core/config.py` — `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
  - `app/services/email_service.py` — provider selection, recipient validation, send orchestration
  - `POST /api/v1/email/send` — body `{ workflowId }`; loads workflow from MongoDB; returns send status
  - `uv add resend`
  - Immediate send only (first `send_email` step); no Celery scheduling or webhooks
  - Recipients read from `workflow_definition.recipient_emails` or `workflow_definition.recipients` in MongoDB

## In Progress

- Nothing.

## Next Up (when user asks to code)

1. Persist uploaded recipients to MongoDB and sync into `workflow_definition` for send
2. Wire remaining frontend areas (dashboard, recipients, review) to backend APIs
3. Resend webhooks + workflow scheduling (out of scope for spec 19)

## Open Questions

- Default Groq model: `openai/gpt-oss-120b` in config (override via `GROQ_MODEL`; `deepseek-r1-distill-llama-70b` decommissioned on Groq)
- Resend: use `RESEND_FROM_EMAIL=onboarding@resend.dev` for dev; production needs verified domain
- Send requires `recipient_emails` or `recipients` on stored `workflow_definition` until recipient upload persists to MongoDB
- `workflow_runs` created at activation vs lazy?

## Architecture Decisions

See `ARCHITECTURE_DECISIONS.md` (ADR-001–011).

## Session Notes

- **Cursor entry:** `Agent.md`
- **Working context:** `context/` (6 files)
- **Design specs:** `docs/` only — no duplicate copies
- Auth uses `@clerk/clerk-react` + `react-router-dom` guards (Vite SPA; not React Router framework middleware).
- Create Workflow → `/workflows/new` shows AI prompt screen first; other `:workflowId` values open builder directly with default mock chat.
- Builder route accepts any `:workflowId`; no data fetch or validation yet.
- Chat replies on send come from `POST /api/v1/chat/message` via LangGraph + Groq; in-memory state per `user_id` + `workflowId`; graceful fallback if Groq unavailable.
- When business goal, product, audience, and CTA are collected, LangGraph generates workflow JSON then email copy for all send steps; chat response includes workflow with nested email content; preview shows subject and snippet from `final_user_version`.
- Email Review panel (below workflow preview) lets users edit subject/HTML/plain text; edits save to backend conversation state and local draft; later chat messages do not regenerate workflow or overwrite user-edited emails.
- `POST /api/v1/email/send` sends first `send_email` step via Resend when `RESEND_API_KEY` is set and workflow definition includes recipients in MongoDB.
- Before workflow generation, preview falls back to keyword-derived `deriveWorkflowFromChat` (local only).
- Recipient valid/invalid counts accumulate per workflow in mock storage; valid recipients persist across page session.
- Review page at `/workflows/:workflowId/review` uses static mock data; Approve button has no backend handler yet.
- Drafts keyed by `workflow-draft:{workflowId}`; `/workflows/new` uses id `new`. Clear Draft on new workflow returns to AI prompt screen.
- Backend protected routes require `Authorization: Bearer <Clerk JWT>`; set `CLERK_PEM_PUBLIC_KEY` in `backend/.env` for token verification. Swagger at `/docs`. Frontend attaches Clerk JWT via `ApiAuthSetup` in `AppLayout`.
