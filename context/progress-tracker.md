# Progress Tracker

Update after every meaningful implementation change.

## Current Phase

**End-to-end builder pipeline (specs 34–36)** — Campaign collection → workflow → emails → review → activation are implemented on backend + core UI.

## Current Goal

Persist uploaded recipients to MongoDB and sync into `workflow_definition` for activation/send, or wire dashboard list to live workflow APIs when requested.

## Builder pipeline (implementation order)

| Step | Spec | Status |
|------|------|--------|
| 1. Campaign collection | `34-campaign-collection-agent.md` | Done |
| 2. Campaign brief + approval | `15.2-campaign-brief-stage.md`, `28-campaign-brief-v2.md` | Done |
| 3. Workflow generation | `15-workflow-generation-agent.md` | Done |
| 4. Email generation | `16-email-generation-agent.md` | Done |
| 5. Review + approval | `35-workflow-review-stage.md`, `09-workflow-review.md` | Done |
| 6. Activation | `36-workflow-activation.md`, `21-celery-redis-queue.md` | Done |
| 7. Execution (post-activate) | `20-workflow-execution-engine.md`, `21-celery-redis-queue.md` | Done |
| 8. Reply handling | `37-reply-handling.md`, `31-reply-intent-model.md`, `22-webhook-processing.md` | Done |
| 9. Agent tools | `44-agent-tools-system.md`, `30-agent-tools-preview.md` | Done |
| 10. E2E integration tests | `45-end-to-end-testing.md` | Done |
| State / stages | `33-langgraph-state-management.md` | Done |

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
- **Workflow review UI (feature spec `09-workflow-review.md`):**
  - `/workflows/:workflowId/review` — `WorkflowReviewPage` with API + mock lead extras
  - `components/review/workflow-review.tsx` — summary sections + Looks Good / Edit / Regenerate / Activate
  - `components/builder/workflow-review-panel.tsx` — same actions in builder preview
  - `types/workflow-review.ts`, `services/review.service.ts`
  - `mocks/workflow-review.ts` — lead status/details when API omits them
- **Workflow review stage (feature spec `35-workflow-review-stage.md`):**
  - `review_actions.py`, `review_service.py` — approve, edit campaign, regenerate workflow
  - `GET /api/v1/review/{id}`, `POST …/approve`; chat short-circuits on review phrases
  - `review_status` on conversation (MongoDB); stage `review` → `activation` when approved
  - Activation blocked until `review_status === "approved"` (403 on activate API)
  - Chat thread returns `reviewStatus`, `activationAllowed`
  - `backend/tests/test_review_stage.py`
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
- **Campaign collection agent (feature spec `34-campaign-collection-agent.md`):**
  - `app/agents/campaign_collection_agent.py` — extract, merge state, skip/delegate, `missing_fields`
  - `app/services/campaign_field_policy.py` — complements `25-optional-fields-and-skip-handling.md`
  - LangGraph: `extract_information` → `missing_information` → question / brief / workflow paths
  - Follow-up delay required after product; no repeat questions for skipped fields
  - `backend/tests/test_campaign_collection_agent.py`
- **Workflow generation agent (feature spec `15-workflow-generation-agent.md`):**
  - `app/agents/workflow_agent.py` — `{ steps: [] }` with `send_email`, `wait`, `reply_condition`, branches
  - `app/services/workflow_structure.py` — `normalize_for_execution()`, follow-up delay on wait steps
  - LangGraph `generate_workflow_node`; routing fix (no regenerate on every post-brief chat message)
  - Persisted to MongoDB; frontend preview from API
  - `backend/tests/test_workflow_generation.py`
- **Email generation agent (feature spec `16-email-generation-agent.md`):**
  - `app/agents/email_generation_agent.py` / `copywriter_agent.py` — promotional, follow-up, reply emails
  - `email_template_repository` — MongoDB `email_templates`; sync from workflow in `persistence.py`
  - `generate_emails_node`; sets `review_status: pending` after generation
  - `backend/tests/test_email_generation_agent.py`
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
  - `EmailProvider` + `ResendProvider` — async send with `workflow_id` / `lead_id` tags
  - `EmailService.send_email` — single lead; stores `resend_message_id`, `workflow_id`, `lead_id` in `email_messages`
  - `EmailService.send_bulk_email` — one Resend id per lead; used by `send_workflow_email` and bulk API path
  - Per-message tracking: `sent`, `delivered`, `opened`, `clicked`, `replied`, `failed` (webhooks via `record_delivery_event`)
  - Workflow analytics counters unchanged (`sent`, `delivered`, etc. on `analytics` collection)
  - `workflow_execution_service` sends through `EmailService` (not raw provider)
  - `POST /api/v1/email/send` — returns `messageId` + `messageIds`
  - `backend/tests/test_resend_email_service.py`
  - Requires `RESEND_API_KEY`; webhooks need `RESEND_WEBHOOK_SECRET` for tracking updates
- **Workflow execution engine (feature spec `20-workflow-execution-engine.md`):**
  - Architecture: API activate → Redis → Celery → `WorkflowExecutionService`
  - Per-recipient `workflow_runs`; one step per `execute_step`
  - **send_email** — `EmailService`; chains to wait scheduling when next step is `wait`
  - **wait** — `next_execution_at` via `follow_up_delay_to_timedelta` (hours, days, weeks)
  - **follow-up** — `send_email` on `no` branch after `reply_condition` (no reply)
  - **condition** — webhook or explicit `condition_result`; yes/no branches
  - Active workflows load frozen definition from `workflow_versions` (`active_version`)
  - `process_due_runs()` — safety enqueue for overdue waits
  - `backend/tests/test_workflow_execution_service.py`, `test_workflow_execution_wait_durations.py`
- **Celery + Redis queue (feature spec `21-celery-redis-queue.md`):**
  - `execute_workflow_step_task`, `resume_workflow_task` (`eta` for waits), `send_email_task`
  - `dispatch.py` chains queued steps after each execution
  - Activation enqueues one task per recipient (spec 36)
  - `backend/tests/test_celery_queue.py`
  - Worker: `uv run celery -A app.workers.celery_app worker -l info -Q workflow_queue,email_queue,retry_queue`
- **Workflow activation (feature spec `36-workflow-activation.md`):**
  - `workflow_version_service` — immutable snapshot in `workflow_versions` on activate
  - `workflow_repository.activate()` — `draft`/`awaiting_activation` → `active`, `activated_at`, `active_version`
  - `execution_repository` — per-lead rows in `executions`; `workflow_runs` for engine + Celery enqueue
  - `POST /api/v1/workflows/{id}/activate` — requires review approval; returns `activeVersion`, `activatedAt`, `executionsCreated`
  - Recipients from `workflow_definition` or conversation `recipients`
  - Frontend `activateWorkflow()` + **Activate Workflow** in review panel / review page
  - `backend/tests/test_activation_flow.py`
- **Resend webhook processing (feature spec `22-webhook-processing.md`):**
  - `POST /api/v1/webhooks/resend` — Resend webhook endpoint (no Clerk auth; Svix signature verification)
  - `app/core/config.py` — `RESEND_WEBHOOK_SECRET`
  - `app/models/webhook_event.py` — event type, timestamp, recipient, workflow
  - `app/repositories/webhook_event_repository.py` — MongoDB `webhook_events` with unique `event_id` dedupe
  - `app/services/webhook_processing_service.py` — validate signature, persist events, evaluate `reply_received` conditions
  - Supported events: delivered, opened, clicked, replied (`email.received`), bounced
  - Reply webhooks advance active workflow runs on `reply_received` condition → yes branch via Celery dispatch
  - `backend/tests/test_webhook_processing.py` — signature validation, dedupe, reply routing, delivered storage, reply classification flags
  - Reply handling on `replied`: LangGraph classify → `inbound_replies` + `leads` upsert (`37-reply-handling.md`)
  - `uv add svix`
- **Reply handling (feature spec `37-reply-handling.md`):**
  - `ReplyIntent` — `interested`, `not_interested`, `need_more_info`, `book_demo`
  - `reply_intent_agent.py` — Groq + keyword fallback; `reply_graph.py` single-node LangGraph
  - `reply_handling_service.py` — webhook text extraction, graph invoke, persist inbound reply, upsert lead
  - `inbound_reply_repository.py`, `lead_repository.py` — MongoDB `inbound_replies`, `leads`
  - `webhook_processing_service` — `reply_classified`, `reply_intent`, `lead_updated` on `WebhookProcessResult`
  - Indexes: unique `leads(workflow_id, email)`; `inbound_replies(workflow_id, created_at)`
  - `backend/tests/test_reply_handling.py`
- **Agent tools system (feature spec `44-agent-tools-system.md`):**
  - `CompanyKnowledgeTool`, `CalendarBookingTool` — campaign context + booking URL
  - `tool_router_agent.py` — Groq tool selection with keyword fallback
  - `agent_tools_graph.py` — LangGraph `select_tool` → `execute_tool`
  - `tool_execution_repository.py` — MongoDB `tool_executions` history
  - Wired into `reply_handling_service` on every inbound reply
  - `POST /api/v1/workflows/{id}/agent-tools/run`, `GET .../history`
  - `CALENDAR_BOOKING_URL` config; webhook fields `tool_called`, `selected_tool`, `agent_response`
  - `backend/tests/test_agent_tools.py`
- **End-to-end integration tests (feature spec `45-end-to-end-testing.md`):**
  - `tests/integration/test_e2e_scenarios.py` — four scenarios with in-memory repos + mock email (no MongoDB/Redis setup)
  - Scenario 1: campaign → review approval → activation → initial email sent
  - Scenario 2: no reply → wait → follow-up email
  - Scenario 3: reply → intent + agent tool → auto-response email (`reply_handling_service._send_auto_response`)
  - Scenario 4: send failure → retry path → success
  - Run: `uv run pytest tests/integration/test_e2e_scenarios.py -v`
- **Workflow analytics (feature spec `23-analytics.md`):**
  - `app/models/analytics.py` — `WorkflowAnalytics` metrics model
  - `app/repositories/analytics_repository.py` — MongoDB `analytics` collection with `$inc` upserts
  - `app/services/analytics_service.py` — increment metrics, webhook mapping, user-scoped reads
  - `GET /api/v1/analytics/{workflow_id}` — returns `sent`, `delivered`, `opened`, `clicked`, `replied`, `failed`, `bounced`
  - Webhook processing increments metrics on new events when `workflow_id` is known
  - `sent` / `failed` updated from workflow execution sends and `POST /api/v1/email/send`
  - `app/core/database.py` — unique index on `workflow_id`
  - `frontend/src/services/analytics.service.ts`, `hooks/use-analytics.ts` — TanStack Query with 30s refetch
  - `WorkflowCardWithAnalytics` on dashboard — shows metrics for active/completed workflows
  - `backend/tests/test_analytics.py` — metric mapping, GET defaults, webhook analytics wiring
- **Follow-up delay (feature spec `26-follow-up-delay.md`):**
  - `app/schemas/follow_up_delay.py`, `app/services/follow_up_delay.py` — parse hours/days/weeks, format preview labels, apply to workflow wait steps
  - Campaign collection asks: "If a recipient does not reply, when should I send the follow-up?" after product/service is known
  - `follow_up_delay` on conversation state, MongoDB, and `workflow_definition` JSON (`{ value, unit }`)
  - `WorkflowDefinition.follow_up_delay` + execution service schedules waits via `timedelta` (hours/days/weeks)
  - Frontend draft + `parse-workflow-definition` + `workflow-preview` — dynamic "Wait N Hours/Days/Weeks" (no hardcoded 3 days)
  - `backend/tests/test_follow_up_delay.py`, `test_follow_up_delay_collection.py`; policy tests updated for delay step
- **Campaign brief v2 (feature spec `28-campaign-brief-v2.md`):**
  - `CampaignBriefData` / `CampaignBriefFieldData` — Campaign Name, Product, Audience, CTA, Tone, Landing Page, Image URL, Follow-Up Delay, Reply Handling, Tools Available
  - `format_follow_up_delay_brief` — brief display e.g. `3 Days`; `DEFAULT_REPLY_HANDLING` = AI Auto Reply; tools = Company Information, Demo Booking
  - `build_campaign_brief` — v2 fields from campaign state + `follow_up_delay`; legacy brief keys still hydrate `campaign_from_brief_dict`
  - `campaign-brief-panel.tsx` — all spec fields + Tools Available checklist; labels match spec
  - `backend/tests/test_campaign_brief_v2.py` — field population and formatted brief text
- **Lead status model (feature spec `29-lead-status-model.md`):**
  - `frontend/src/types/lead-status.ts` — `LEAD_STATUSES`, `LeadStatus` type, display labels (NEW through CLOSED)
  - `backend/app/schemas/enums.py` — `LeadStatus` (`pending`, `emailed`, `replied`, `interested`, `booked_demo`, `not_interested`)
  - Reply handling maps `ReplyIntent` → `LeadStatus` and upserts `leads` by workflow + email
  - `types/workflow-review.ts` — `LeadStatusCounts` on review data model
  - `mocks/workflow-review.ts` — mock per-status recipient counts
  - `components/review/workflow-review.tsx` — **Lead Status** section with outlined chips per status
- **AI reply agent preview (feature spec `27-ai-reply-agent-preview.md`):**
  - `workflow-preview.tsx` — for `reply_received` conditions: Yes branch shows **AI Reply Agent** (not backend yes-step label)
  - **Auto Send Response** chip, **Max Reply Count: 2**, and note that conversation completes after 2 AI responses
  - Condition label **Reply?** in preview; No branch unchanged (follow-up step from API)
  - `workflow-definition-to-state.ts`, `workflow-state.ts` — draft yes-branch label **AI Reply Agent** when condition is `reply_received`
  - UI only; no backend or execution changes
- **Agent tools preview (feature spec `30-agent-tools-preview.md`):**
  - `workflow-preview.tsx` — `AiReplyAgentStep` shows **Available Tools:** checklist (✓ Company Information, ✓ Demo Booking)
  - Reuses `DEFAULT_TOOLS_AVAILABLE` from `types/campaign-brief.ts` (matches campaign brief v2)
  - Backend execution in spec `44-agent-tools-system.md`
- **Reply intent model (feature spec `31-reply-intent-model.md`):**
  - `backend/app/schemas/reply_intent.py` — `ReplyIntent` enum (four webhook classifications)
  - `frontend/src/types/reply-intent.ts` — legacy display labels for review UI
  - `types/lead-details.ts` — `LeadDetails` model with optional `intent`
  - `components/leads/lead-details.tsx` — intent chip when available; `LeadDetailsList` for multiple leads
  - `mocks/lead-details.ts` — mock leads (mix of classified and unclassified)
  - `components/review/workflow-review.tsx` — **Lead Details** section on review page
- **Conversation thread preview (feature spec `32-conversation-thread-preview.md`):**
  - `frontend/src/types/conversation-thread.ts` — `ConversationMessageType`, `ConversationThreadMessage`, display labels (Agent Message, Prospect Reply, Agent Response)
  - `frontend/src/mocks/conversation-thread.ts` — mock thread in chronological order
  - `frontend/src/components/conversation/conversation-thread.tsx` — **Thread View** with labeled messages
  - `workflow-preview.tsx` — thread shown inside **AI Reply Agent** step
  - UI only; no backend integration
- **Optional fields and skip handling (feature spec `25-optional-fields-and-skip-handling.md`):**
  - `app/services/campaign_field_policy.py` — skip phrase detection, `skipped_fields`, intelligent defaults, minimal product inference
  - Only `product_info` required for workflow; optional: goal, tone, audience, CTA, landing page, images, attachments, competitors
  - Defaults: Product Promotion, Professional, General Customers, Learn More
  - `build_collection_reply` — assumptions block + customize prompt when product known; no repeat asks for skipped fields
  - `skipped_fields` persisted in MongoDB conversations
  - `backend/tests/test_campaign_field_policy.py` — skip, defaults, minimal inference, assumptions UX
- **LangGraph state management (feature spec `33-langgraph-state-management.md`):**
  - `ConversationState` — `messages`, `campaign_brief`, `workflow`, `email_templates`, `recipients`, `missing_fields`, `brief_status`, `review_status`, `regenerate_workflow`
  - Stages: `discovery`, `campaign_brief`, `workflow_generation`, `email_generation`, `review`, `activation` (`app/schemas/conversation_stage.py`)
  - `conversation_state_service.py` — normalize/sanitize on load and save; strip stale workflow/brief previews by stage
  - `conversation_stage.py` — derive `current_stage` from artifacts and brief approval
  - `persistence.py` + `conversation_repository.py` — persist after every chat message; MongoDB is source of truth
  - `GET /api/chat/thread/{threadId}`, `POST /api/chat/reset` — reload and reset conversation state
  - `workflow_session_service.initialize_empty_session` — fresh state on `POST /api/v1/workflows`
  - Frontend `useChatThread` always loads server state on refresh; local draft only hydrates recipients
  - `builder-boot.ts` — server thread overrides localStorage for messages/workflow/brief (fixes stale preview / wrong campaign)
  - `backend/tests/test_langgraph_state_management.py`, `test_chat_stage.py`, `test_chat_thread_service.py`
- **LangSmith observability (feature spec `24-langsmith-observability.md`):**
  - `app/core/langsmith_tracing.py` — enables `LANGCHAIN_TRACING_V2` from `LANGSMITH_API_KEY` at app startup
  - `app/core/langsmith_usage.py` — records Groq token usage on LangSmith runs
  - `app/core/config.py` — `LANGSMITH_API_KEY`, `LANGCHAIN_PROJECT`, `ENABLE_LANGSMITH_TRACING`
  - `app/main.py` — calls `setup_langsmith_tracing()` before API routers load
  - `@traceable` on `GroqProvider.generate`, `extract_campaign_data`, workflow agent, copywriter agent
  - `chat_service.py` — LangGraph `ainvoke` with `run_name` and `workflow_id` / `user_id` metadata
  - `backend/.env.example` — LangSmith env vars documented
  - `uv add langsmith` (explicit dependency)
  - `backend/tests/test_langsmith_tracing.py` — setup and settings coverage

## In Progress

- Nothing.

## Next Up (when user asks to code)

1. Persist uploaded recipients to MongoDB (`POST /api/v1/recipients/upload` → conversation + `workflow_definition`)
2. Wire dashboard workflow list to `GET /api/v1/workflows` (replace mocks)
3. Real lead status / lead details on review API (replace review-page mocks)

## Open Questions

- Default Groq model: `openai/gpt-oss-120b` in config (override via `GROQ_MODEL`; `deepseek-r1-distill-llama-70b` decommissioned on Groq)
- Resend: use `RESEND_FROM_EMAIL=onboarding@resend.dev` for dev; production needs verified domain
- Resend webhooks: set `RESEND_WEBHOOK_SECRET=whsec_...` from Resend dashboard; endpoint is `POST /api/v1/webhooks/resend`
- Send/activate requires `recipient_emails` on `workflow_definition` or `recipients` on conversation state until CSV upload persists to MongoDB
- Activation (spec 36): review approval required; creates `workflow_versions` snapshot, `executions` + `workflow_runs`, sets `activated_at`; needs Redis + Celery worker
- LangSmith tracing is off when `LANGSMITH_API_KEY` is empty or `ENABLE_LANGSMITH_TRACING=false`

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
- When product/service is known (optional fields may use defaults or skips), LangGraph builds campaign brief then workflow + email copy after brief approval; chat response includes workflow with nested email content; preview shows subject and snippet from `final_user_version`.
- Email Review panel (below workflow preview) lets users edit subject/HTML/plain text; edits save to backend conversation state and local draft; later chat messages do not regenerate workflow or overwrite user-edited emails.
- `POST /api/v1/email/send` sends first `send_email` step to all workflow recipients via `send_bulk_email`; each send stored in `email_messages` with Resend message id.
- Workflow execution after activate runs in Celery workers (not in the API thread). Wait steps use `resume_workflow_task` with Celery `eta` (hours/days/weeks). Follow-up emails run on the no-reply branch after the wait + condition.
- Resend webhooks at `POST /api/v1/webhooks/resend` persist events, classify replies (intent + lead status), and evaluate `reply_received` conditions on active runs.
- `GET /api/v1/analytics/{workflow_id}` returns per-workflow counters; webhooks and sends update the `analytics` collection.
- Dashboard active/completed cards poll analytics every 30s via `useAnalytics`.
- LangSmith: set `LANGSMITH_API_KEY` in `backend/.env` (optional `LANGCHAIN_PROJECT`, `ENABLE_LANGSMITH_TRACING`); traces appear in LangSmith for chat/graph runs when key is set.
- Follow-up delay is required after product/service before the campaign brief; user can answer e.g. `3 days` or `4 hours`.
- Workflow preview: `reply_received` → **Reply?** with Yes = **AI Reply Agent** (auto-send badge, max 2 replies, Available Tools checklist); No = follow-up email step from definition.
- Campaign brief v2: right panel shows Product, Follow-Up Delay (from state), Reply Handling (AI Auto Reply), and Tools Available checklist; updates on each chat response while pending approval.
- Workflow review: API-backed summary on `/workflows/:id/review`; **Lead Status** / **Lead Details** still use mocks where API has no lead analytics yet (spec 35 done, lead backend TBD).
- Review actions: Looks Good (approve), Edit Campaign, Regenerate Workflow via chat; Activate when `activationAllowed` (spec 36).
- Workflow preview: **AI Reply Agent** includes **Thread View** with mock Agent Message → Prospect Reply → Agent Response in chronological order.
- Conversation state persists in MongoDB per `(user_id, workflow_id)`; page refresh loads `GET /api/chat/thread/{id}` (not localStorage draft for chat/workflow/brief).
- New workflow (`POST /api/v1/workflows`) initializes empty conversation state; Clear Draft calls `POST /api/chat/reset`.
- Stage-aware previews: workflow hidden until post-brief generation; brief shown from `campaign_brief` stage onward.
- Before workflow generation, preview shows empty state (no keyword-derived diagram).
- Recipient valid/invalid counts accumulate per workflow in mock storage; valid recipients persist across page session.
- Review approve: chat phrase or `POST /api/v1/review/{id}/approve`; activation via `POST /api/v1/workflows/{id}/activate` after approval.
- Drafts keyed by `workflow-draft:{workflowId}`; `/workflows/new` uses id `new`. Clear Draft on new workflow returns to AI prompt screen.
- Backend protected routes require `Authorization: Bearer <Clerk JWT>`; set `CLERK_PEM_PUBLIC_KEY` in `backend/.env` for token verification. Swagger at `/docs`. Frontend attaches Clerk JWT via `ApiAuthSetup` in `AppLayout`.
