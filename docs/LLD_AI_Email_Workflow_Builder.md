# Low Level Design (LLD)

# AI-Driven Email Workflow Builder

**Version:** MVP v1
**Purpose:** Implementation-ready reference for Cursor AI — defines exact folder structure, schemas, service contracts, task signatures, and code patterns required to build the system.

---

## 1. Tech Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| **Frontend** | React | v19 |
| **Frontend** | TypeScript | Strict mode |
| **Frontend UI** | MUI (Material UI) | v6 — components, theme, layout |
| **Frontend Data** | TanStack Query (React Query) | v5 — server state, caching, mutations |
| **Frontend Build** | Vite | Dev server + production bundle |
| **Frontend Auth** | Clerk React SDK | JWT-based |
| **Backend** | Python | 3.12+ (3.14 target) |
| **Backend Package Manager** | uv | `pyproject.toml` + lockfile — no pip/poetry |
| **Backend Framework** | FastAPI | Async |
| **AI Orchestration** | LangGraph + LangChain | Multi-agent graph |
| **LLM Provider** | Groq (DeepSeek-R1 / GPT-OSS-120B) | Swappable via provider pattern |
| **Database** | MongoDB | Motor (async driver) |
| **Queue** | Redis | Task buffer |
| **Background Jobs** | Celery | Async workers |
| **Email Provider** | Resend | Webhooks enabled |
| **Monitoring** | LangSmith | Agent + prompt tracing |

---

## 2. Monorepo Layout

```
/
├── frontend/                 # React + Vite + MUI + TanStack Query
├── backend/                  # Python + uv + FastAPI
│   ├── pyproject.toml
│   ├── uv.lock
│   └── app/
├── docs/
├── .env.example
└── ARCHITECTURE_DECISIONS.md
```

### Backend setup (uv)

```bash
cd backend
uv sync                    # install deps from pyproject.toml + uv.lock
uv run uvicorn app.main:app --reload --port 8000
uv run celery -A app.workers.celery_app worker -l info
```

> **Cursor rule:** Use `uv add <package>` to add dependencies. Do not hand-edit `uv.lock`. Do not use `pip install` in this project.

---

## 3. Backend Folder Structure

```
backend/app/
│
├── api/                          # FastAPI route handlers (thin layer — no business logic)
│   ├── chat.py                   # POST /api/chat
│   ├── workflow.py               # POST /api/workflow, /activate, /pause
│   ├── recipients.py             # POST /api/recipients/upload
│   ├── analytics.py              # GET /api/analytics/{workflow_id}
│   └── webhook.py                # POST /api/webhooks/resend
│
├── services/                     # Business logic layer
│   ├── ai_service.py             # Orchestrates LangGraph calls
│   ├── workflow_service.py       # Workflow CRUD + state transitions
│   ├── recipient_service.py      # CSV parsing, validation, storage
│   ├── analytics_service.py      # Metrics aggregation
│   └── email_service.py          # Resend API abstraction
│
├── repositories/                 # MongoDB access layer (no business logic)
│   ├── workflow_repository.py
│   ├── conversation_repository.py
│   ├── recipient_repository.py
│   ├── analytics_repository.py
│   └── webhook_repository.py
│
├── agents/                       # Individual LangGraph agent definitions
│   ├── supervisor_agent.py       # Routes between agents
│   ├── campaign_agent.py         # Collects business goal + product info
│   ├── audience_agent.py         # Collects target audience
│   ├── content_agent.py          # Collects tone, CTA, email style
│   ├── workflow_agent.py         # Builds workflow step definitions
│   ├── copywriter_agent.py       # Generates subject, HTML, plain text
│   ├── review_agent.py           # Quality + tone + grammar review
│   └── validation_agent.py       # Validates recipient CSV data
│
├── langgraph/                    # LangGraph graph wiring
│   ├── graph.py                  # StateGraph definition + edge routing
│   ├── state.py                  # CampaignState TypedDict
│   └── nodes.py                  # Node functions called by the graph
│
├── workers/                      # Celery task definitions
│   ├── email_worker.py           # send_email_task, retry_email_task
│   └── workflow_worker.py        # execute_workflow_step_task, resume_workflow_task
│
├── providers/                    # External provider abstractions (swappable)
│   ├── llm/
│   │   ├── base.py               # Abstract LLMProvider class
│   │   └── groq_provider.py      # Groq implementation
│   └── email/
│       ├── base.py               # Abstract EmailProvider class
│       └── resend_provider.py    # Resend implementation
│
├── models/                       # Pydantic models (request/response + DB documents)
│   ├── workflow.py
│   ├── workflow_run.py
│   ├── conversation.py
│   ├── recipient.py
│   ├── analytics.py
│   └── webhook_event.py
│
├── core/                         # App-wide configuration and utilities
│   ├── config.py                 # Settings from environment variables (pydantic-settings)
│   ├── database.py               # MongoDB Motor client + connection setup
│   ├── security.py               # Clerk JWT verification middleware
│   └── logger.py                 # Structured logging setup
│
└── main.py                       # FastAPI app factory + router registration
```

> **Cursor rule:** Keep API handlers thin. All logic lives in services. Repositories handle only MongoDB reads/writes — no conditional logic.

---

## 4. Frontend Folder Structure

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx                    # QueryClientProvider + ThemeProvider + ClerkProvider
    ├── App.tsx                     # React Router routes
    ├── theme/
    │   └── muiTheme.ts             # MUI createTheme (palette, typography)
    ├── api/
    │   ├── client.ts               # fetch wrapper + Clerk getToken()
    │   ├── queryKeys.ts            # Centralized TanStack Query keys
    │   └── hooks/
    │       ├── useChat.ts          # useMutation — POST /api/chat
    │       ├── useWorkflows.ts     # useQuery — GET /api/workflows
    │       ├── useWorkflow.ts      # useQuery — single workflow
    │       ├── useRecipients.ts    # useMutation — CSV upload
    │       ├── useActivateWorkflow.ts
    │       └── useAnalytics.ts     # useQuery — GET /api/analytics/:id
    ├── providers/
    │   └── QueryProvider.tsx       # QueryClientProvider config
    ├── components/                 # MUI-based shared UI
    │   ├── layout/
    │   │   ├── AppShell.tsx        # AppBar + Drawer + Outlet
    │   │   └── PageHeader.tsx
    │   └── common/
    │       ├── LoadingState.tsx
    │       └── ErrorAlert.tsx
    └── pages/
        ├── LoginPage.tsx
        ├── DashboardPage.tsx
        ├── CreateCampaignPage.tsx
        ├── BuilderPage.tsx
        ├── ReviewPage.tsx
        └── AnalyticsPage.tsx
```

### TanStack Query conventions

| Pattern | Usage |
|---|---|
| `useQuery` | GET workflows, analytics, workflow detail |
| `useMutation` | POST chat, upload CSV, activate/pause workflow |
| `queryKeys` | `['workflows']`, `['workflow', id]`, `['analytics', id]` |
| Invalidation | After `activate` → invalidate `['workflow', id]` and `['analytics', id]` |
| Auth header | `apiClient` attaches `Authorization: Bearer <clerk_token>` per request |

```typescript
// frontend/src/api/queryKeys.ts
export const queryKeys = {
  workflows: ['workflows'] as const,
  workflow: (id: string) => ['workflow', id] as const,
  analytics: (id: string) => ['analytics', id] as const,
  conversation: (id: string) => ['conversation', id] as const,
};
```

> **Cursor rule:** No raw `fetch` in page components. All API calls go through `api/client.ts` + TanStack Query hooks. UI uses MUI components only (no second component library).

---

## 5. MongoDB Collections

| Collection | Purpose |
|---|---|
| `users` | User identity synced from Clerk |
| `conversations` | Full AI chat history per session |
| `workflows` | Workflow definitions and state |
| `email_templates` | AI-generated email content per workflow step |
| `recipients` | Uploaded/manual recipient list per workflow |
| `workflow_runs` | Per-recipient execution state |
| `analytics` | Aggregated engagement metrics per workflow |
| `webhook_events` | Raw Resend events (audit + debugging) |

---

## 6. Collection Schemas

### `users`

```python
{
  "_id": ObjectId,
  "clerk_user_id": str,          # Clerk's user identifier — used for JWT validation
  "email": str,
  "created_at": datetime
}
```

**Index:** `clerk_user_id` (unique)

---

### `conversations`

```python
{
  "_id": ObjectId,
  "user_id": ObjectId,           # Reference → users._id
  "workflow_id": ObjectId,       # Reference → workflows._id (null until workflow created)
  "messages": [
    {
      "role": str,               # "user" | "assistant"
      "content": str,
      "timestamp": datetime
    }
  ],
  "campaign_state": {            # Mirrors CampaignState — persisted between turns
    "business_goal": str,
    "audience": str,
    "tone": str,
    "cta": str,
    "workflow_definition": dict,
    "current_stage": str         # Which agent is currently active
  },
  "created_at": datetime,
  "updated_at": datetime
}
```

**Index:** `user_id`, `workflow_id`

---

### `workflows`

```python
{
  "_id": ObjectId,
  "user_id": ObjectId,           # Reference → users._id
  "name": str,
  "status": str,                 # "draft" | "generating" | "awaiting_approval" | "active" | "paused" | "completed" | "archived"
  "workflow_definition": {       # Generated by Workflow Designer Agent
    "steps": [
      {
        "step_id": str,          # Unique step identifier e.g. "step_1"
        "type": str,             # "send_email" | "wait" | "condition" | "end"
        "config": dict           # Step-specific config (see Workflow Definition section)
      }
    ]
  },
  "created_at": datetime,
  "updated_at": datetime
}
```

**Index:** `user_id`, `status`

---

### `email_templates`

```python
{
  "_id": ObjectId,
  "workflow_id": ObjectId,       # Reference → workflows._id
  "step_id": str,                # Maps to workflow_definition.steps[n].step_id
  "version": int,                # Increments on each regeneration — always use latest
  "subject": str,
  "html_content": str,
  "plain_text_content": str,
  "created_at": datetime
}
```

**Index:** `workflow_id`, `step_id`, `version`
**Query pattern:** Always fetch `MAX(version)` per `workflow_id + step_id`

---

### `recipients`

```python
{
  "_id": ObjectId,
  "workflow_id": ObjectId,       # Reference → workflows._id
  "batch_id": str,               # Groups recipients from same upload
  "name": str,
  "email": str,
  "status": str,                 # "valid" | "invalid" | "skipped"
  "reply_received": bool,        # Updated by webhook processor
  "created_at": datetime
}
```

**Index:** `workflow_id`, `email` (unique per workflow), `status`

---

### `workflow_runs`

```python
{
  "_id": ObjectId,
  "workflow_id": ObjectId,       # Reference → workflows._id
  "recipient_id": ObjectId,      # Reference → recipients._id
  "current_step_id": str,        # Maps to workflow_definition step_id
  "status": str,                 # "queued" | "running" | "waiting" | "completed" | "failed"
  "next_execution_at": datetime, # Set for wait steps — Celery eta target
  "last_email_sent_at": datetime,
  "created_at": datetime,
  "updated_at": datetime
}
```

**Index:** `workflow_id`, `recipient_id`, `status`, `next_execution_at`

---

### `analytics`

```python
{
  "_id": ObjectId,
  "workflow_id": ObjectId,       # Reference → workflows._id
  "sent": int,
  "delivered": int,
  "opened": int,
  "clicked": int,
  "replied": int,
  "failed": int,
  "bounced": int,
  "updated_at": datetime
}
```

**Index:** `workflow_id` (unique — one document per workflow, use $inc to update)

---

### `webhook_events`

```python
{
  "_id": ObjectId,
  "event_type": str,             # "delivered" | "opened" | "clicked" | "replied" | "bounced" | "failed"
  "resend_message_id": str,      # Resend's internal message ID
  "workflow_id": ObjectId,       # Resolved from message_id lookup
  "recipient_id": ObjectId,      # Resolved from email address
  "payload": dict,               # Full raw Resend webhook payload
  "processed": bool,
  "received_at": datetime
}
```

**Index:** `resend_message_id`, `processed`, `event_type`

---

## 7. LangGraph State

```python
# app/langgraph/state.py

from typing import TypedDict, List, Dict, Any, Optional

class EmailDraft(TypedDict):
    step_id: str
    subject: str
    html_content: str
    plain_text_content: str
    version: int

class WorkflowStep(TypedDict):
    step_id: str
    type: str                    # "send_email" | "wait" | "condition" | "end"
    config: Dict[str, Any]

class CampaignState(TypedDict):
    # Identity
    conversation_id: str
    workflow_id: Optional[str]
    user_id: str

    # Gathered requirements
    business_goal: str
    industry: str
    product_info: str
    audience: str
    tone: str                    # "professional" | "casual" | "urgent" | "friendly"
    cta: str
    email_format: str            # "html" | "plain_text" | "both"
    attachments: List[str]       # File references

    # Generated artifacts
    workflow_definition: List[WorkflowStep]
    generated_emails: List[EmailDraft]

    # Graph control
    current_stage: str           # Which agent runs next
    messages: List[Dict]         # Full conversation history
    requires_more_info: bool     # Supervisor uses this to decide next agent
    review_passed: bool          # Set by Review Agent
```

---

## 8. LangGraph Graph Flow

```python
# app/langgraph/graph.py

from langgraph.graph import StateGraph
from app.langgraph.state import CampaignState

graph = StateGraph(CampaignState)

# Register nodes
graph.add_node("supervisor",         supervisor_node)
graph.add_node("campaign_agent",     campaign_node)
graph.add_node("audience_agent",     audience_node)
graph.add_node("content_agent",      content_node)
graph.add_node("workflow_agent",     workflow_node)
graph.add_node("copywriter_agent",   copywriter_node)
graph.add_node("review_agent",       review_node)

# Entry point
graph.set_entry_point("supervisor")

# Supervisor routes to agents based on what's missing in state
graph.add_conditional_edges("supervisor", route_to_next_agent, {
    "campaign_agent":   "campaign_agent",
    "audience_agent":   "audience_agent",
    "content_agent":    "content_agent",
    "workflow_agent":   "workflow_agent",
    "copywriter_agent": "copywriter_agent",
    "review_agent":     "review_agent",
    "end":              END
})

# All agents return to supervisor after execution
graph.add_edge("campaign_agent",   "supervisor")
graph.add_edge("audience_agent",   "supervisor")
graph.add_edge("content_agent",    "supervisor")
graph.add_edge("workflow_agent",   "supervisor")
graph.add_edge("copywriter_agent", "review_agent")
graph.add_edge("review_agent",     "supervisor")

app_graph = graph.compile()
```

### Agent Routing Logic

```python
# app/langgraph/nodes.py

def route_to_next_agent(state: CampaignState) -> str:
    """Supervisor routing logic — checks what's missing and routes accordingly."""
    if not state["business_goal"] or not state["product_info"]:
        return "campaign_agent"
    if not state["audience"]:
        return "audience_agent"
    if not state["tone"] or not state["cta"]:
        return "content_agent"
    if not state["workflow_definition"]:
        return "workflow_agent"
    if not state["generated_emails"]:
        return "copywriter_agent"
    if not state["review_passed"]:
        return "review_agent"
    return "end"
```

---

## 9. Workflow Definition Structure

```python
# Stored in workflows.workflow_definition

{
  "steps": [
    {
      "step_id": "step_1",
      "type": "send_email",
      "config": {
        "email_step_id": "step_1"    # References email_templates.step_id
      }
    },
    {
      "step_id": "step_2",
      "type": "wait",
      "config": {
        "days": 3
      }
    },
    {
      "step_id": "step_3",
      "type": "condition",
      "config": {
        "condition": "reply_received",
        "yes_step_id": "step_4",     # Next step if YES
        "no_step_id": "step_5"       # Next step if NO
      }
    },
    {
      "step_id": "step_4",
      "type": "end",
      "config": {}
    },
    {
      "step_id": "step_5",
      "type": "send_email",
      "config": {
        "email_step_id": "step_5"
      }
    }
  ]
}
```

---

## 10. Service Layer Contracts

### AIService

```python
# app/services/ai_service.py

class AIService:
    async def process_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str
    ) -> dict:
        """
        Load conversation state → run LangGraph → save state → return reply + preview.
        Returns: { reply, workflow_preview, email_preview, status }
        """

    async def regenerate_email(
        self,
        conversation_id: str,
        step_id: str,
        instruction: str
    ) -> dict:
        """
        Load existing email template → run Copywriter Agent with instruction → save new version.
        Returns: { subject, html_content, plain_text_content, version }
        """
```

---

### WorkflowService

```python
# app/services/workflow_service.py

class WorkflowService:
    async def create(self, user_id: str, conversation_id: str) -> str:
        """Create workflow document. Returns workflow_id."""

    async def activate(self, workflow_id: str, user_id: str) -> dict:
        """
        Validate ownership → set status = active →
        create workflow_runs per recipient →
        push execute_workflow_step_task to Redis.
        Returns: { status, runs_queued }
        """

    async def pause(self, workflow_id: str, user_id: str) -> dict:
        """Set status = paused. Running Celery tasks complete their current step then stop."""

    async def archive(self, workflow_id: str, user_id: str) -> dict:
        """Set status = archived."""
```

---

### RecipientService

```python
# app/services/recipient_service.py

class RecipientService:
    async def upload_csv(
        self,
        workflow_id: str,
        file: UploadFile
    ) -> dict:
        """
        Parse CSV → validate rows → save valid recipients to MongoDB.
        Returns: { total, valid, invalid, invalid_rows, batch_id }
        """

    async def validate_row(self, row: dict) -> tuple[bool, str]:
        """
        Returns (is_valid, reason).
        Checks: email format, not empty, not duplicate within workflow.
        """
```

---

### EmailService

```python
# app/services/email_service.py

class EmailService:
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: str,
        workflow_run_id: str
    ) -> dict:
        """
        Inject personalization variables → call Resend provider → return message_id.
        Raises: EmailDeliveryError on failure (triggers Celery retry).
        """

    def inject_variables(self, content: str, recipient: dict) -> str:
        """
        Replace {{first_name}}, {{company_name}}, {{email}} with recipient values.
        """
```

---

## 11. API Contracts

### POST `/api/chat`

```python
# Request
class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None    # None on first message
    message: str

# Response
class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    workflow_preview: Optional[WorkflowPreview]
    email_preview: Optional[EmailPreview]
    status: str                              # "collecting" | "generating" | "ready"
```

---

### POST `/api/workflow`

```python
# Request
class CreateWorkflowRequest(BaseModel):
    conversation_id: str

# Response
class CreateWorkflowResponse(BaseModel):
    workflow_id: str
    status: str                              # "draft"
```

---

### POST `/api/workflow/activate`

```python
# Request
class ActivateWorkflowRequest(BaseModel):
    workflow_id: str

# Response
class ActivateWorkflowResponse(BaseModel):
    workflow_id: str
    status: str                              # "active"
    runs_queued: int
    message: str
```

---

### POST `/api/workflow/pause`

```python
# Request
class PauseWorkflowRequest(BaseModel):
    workflow_id: str

# Response
class PauseWorkflowResponse(BaseModel):
    workflow_id: str
    status: str                              # "paused"
```

---

### POST `/api/recipients/upload`

```python
# Request: multipart/form-data
#   file: CSV
#   workflow_id: str

# Response
class RecipientUploadResponse(BaseModel):
    total: int
    valid: int
    invalid: int
    invalid_rows: List[InvalidRow]
    batch_id: str

class InvalidRow(BaseModel):
    row: int
    email: str
    reason: str                              # "invalid_format" | "missing_email" | "duplicate"
```

---

### GET `/api/analytics/{workflow_id}`

```python
# Response
class AnalyticsResponse(BaseModel):
    workflow_id: str
    sent: int
    delivered: int
    opened: int
    clicked: int
    replied: int
    failed: int
    bounced: int
    open_rate: str                           # e.g. "48.9%"
    reply_rate: str                          # e.g. "8.4%"
```

---

### POST `/api/webhooks/resend`

```python
# Headers: resend-signature (verify using Resend webhook secret)

# Request body (raw Resend payload)
class ResendWebhookPayload(BaseModel):
    type: str                                # "email.delivered" | "email.opened" | etc.
    data: dict                               # Contains message_id, to, from, etc.

# Response
class WebhookResponse(BaseModel):
    status: str                              # "ok"
```

---

## 12. Celery Task Definitions

```python
# app/workers/workflow_worker.py

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def execute_workflow_step_task(self, workflow_run_id: str):
    """
    Load workflow_run → load current step → execute step action.
    On send_email: call email_worker.send_email_task
    On wait: schedule resume_workflow_task with eta
    On condition: evaluate and route to yes/no branch
    On end: mark workflow_run as completed
    """

@celery_app.task(bind=True, max_retries=3)
def resume_workflow_task(self, workflow_run_id: str):
    """
    Called after wait period elapses.
    Loads workflow_run → advances to next step → calls execute_workflow_step_task.
    """
```

```python
# app/workers/email_worker.py

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300       # 5 min between retries
)
def send_email_task(self, workflow_run_id: str, step_id: str):
    """
    Load recipient + email template → inject variables → call EmailService.send_email.
    On success: update workflow_run, schedule next step.
    On failure: retry up to 3 times → dead letter queue.
    """

@celery_app.task
def process_webhook_task(webhook_event_id: str):
    """
    Load webhook_event → update analytics → update recipient reply status →
    trigger workflow condition evaluation if event is reply.
    """
```

---

## 13. Redis Queue Design

| Queue Name | Used For | Priority |
|---|---|---|
| `workflow_queue` | Workflow step execution jobs | High |
| `email_queue` | Email send jobs | High |
| `retry_queue` | Failed email retries | Medium |
| `webhook_queue` | Webhook processing jobs | High |

```python
# Delayed task example (Wait step)
execute_workflow_step_task.apply_async(
    args=[workflow_run_id],
    queue="workflow_queue",
    eta=datetime.utcnow() + timedelta(days=3)   # Redis holds until eta
)
```

> **No thread sleeps. No polling loops.** All delays use Celery `eta` with Redis as the broker.

---

## 14. Provider Abstraction Pattern

### LLM Provider

```python
# app/providers/llm/base.py

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str) -> str:
        pass

# app/providers/llm/groq_provider.py

class GroqProvider(LLMProvider):
    async def complete(self, prompt: str, system: str) -> str:
        # Groq API call
        ...
```

### Email Provider

```python
# app/providers/email/base.py

from abc import ABC, abstractmethod

class EmailProvider(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, html: str, text: str) -> str:
        """Returns provider message_id."""
        pass

# app/providers/email/resend_provider.py

class ResendProvider(EmailProvider):
    async def send(self, to: str, subject: str, html: str, text: str) -> str:
        # Resend API call
        ...
```

> **Cursor rule:** Never import `GroqProvider` or `ResendProvider` directly in services. Always depend on the abstract base class. Inject the concrete implementation via FastAPI dependency injection.

---

## 15. Authentication & Authorization

```python
# app/core/security.py

from fastapi import Depends, HTTPException, Header
import jwt

async def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Extract Bearer token → verify Clerk JWT → return user payload.
    Raises HTTP 401 if token invalid or expired.
    """
    token = authorization.replace("Bearer ", "")
    payload = jwt.decode(token, CLERK_PEM_PUBLIC_KEY, algorithms=["RS256"])
    return payload

# Usage in route handlers
@router.post("/workflow/activate")
async def activate_workflow(
    request: ActivateWorkflowRequest,
    current_user: dict = Depends(get_current_user)
):
    ...
```

**Authorization rule:** Every repository query that fetches by `workflow_id` must also filter by `user_id`. Never trust the client to enforce ownership.

```python
# CORRECT
workflow = await workflow_repo.find_one({"_id": workflow_id, "user_id": user_id})

# WRONG — never do this
workflow = await workflow_repo.find_one({"_id": workflow_id})
```

---

## 16. Failure Handling

### Email Retry Flow

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_email_task(self, workflow_run_id: str, step_id: str):
    try:
        # attempt send
    except EmailDeliveryError as e:
        if self.request.retries >= self.max_retries:
            # Move to dead letter queue
            dead_letter_queue.push({
                "workflow_run_id": workflow_run_id,
                "step_id": step_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            # Update workflow_run status = "failed"
            return
        raise self.retry(exc=e)
```

| Attempt | Delay | Action on Final Failure |
|---|---|---|
| Attempt 1 | Immediate | Retry |
| Attempt 2 | 5 minutes | Retry |
| Attempt 3 | 5 minutes | Dead Letter Queue + log |

---

## 17. Webhook Signature Validation

```python
# app/api/webhook.py

import hmac, hashlib

def verify_resend_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate that the webhook came from Resend and was not tampered with.
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@router.post("/webhooks/resend")
async def resend_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("resend-signature", "")
    if not verify_resend_signature(payload, signature, settings.RESEND_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    ...
```

---

## 18. Environment Variables

```bash
# app/core/config.py (loaded via pydantic-settings)

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=email_workflow_builder

# Redis
REDIS_URL=redis://localhost:6379

# Clerk
CLERK_PEM_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...

# Groq
GROQ_API_KEY=gsk_...

# Resend
RESEND_API_KEY=re_...
RESEND_WEBHOOK_SECRET=whsec_...

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_PROJECT=email-workflow-builder
```

---

## 19. Monitoring & Observability

### LangSmith (AI tracing)

```python
# Automatically enabled when LANGCHAIN_TRACING_V2=true
# Tracks: agent execution, prompt inputs/outputs, token usage, LLM latency
```

### Application Logging

```python
# app/core/logger.py

import structlog

logger = structlog.get_logger()

# Usage
logger.info("workflow.activated", workflow_id=workflow_id, user_id=user_id, runs=95)
logger.error("email.failed", workflow_run_id=run_id, attempt=3, error=str(e))
```

### Key Metrics to Monitor

| Metric | Alert Threshold |
|---|---|
| Email delivery rate | < 90% |
| Workflow completion rate | < 85% |
| Celery queue depth | > 1000 tasks |
| LLM response latency | > 10 seconds |
| Webhook processing lag | > 30 seconds |

---

## 20. Security Checklist

| Concern | Implementation |
|---|---|
| Transport | HTTPS only — enforce in deployment config |
| Authentication | Clerk JWT on every protected route via `Depends(get_current_user)` |
| Authorization | Filter all DB queries by `user_id` |
| Input validation | Pydantic models on all request bodies |
| Webhook verification | HMAC-SHA256 signature check on `/webhooks/resend` |
| Secrets | All via environment variables — never hardcoded |
| Rate limiting | FastAPI middleware (e.g. `slowapi`) on `/api/chat` and `/api/webhooks/resend` |
| Audit logging | Log all workflow state transitions with `user_id` + `timestamp` |

---

## 21. Scalability Strategy

### MVP Architecture

```
FastAPI → MongoDB → Redis → Celery → Resend
```

### Future Scaling Path

| Upgrade | Why |
|---|---|
| Kafka | Replace Redis for high-throughput webhook event streaming |
| Dedicated Workflow Engine Service | Separate deployment for execution workload |
| MongoDB Sharding | Horizontal data scaling per `user_id` shard key |
| Multiple Worker Pools | Isolated Celery pools: email pool, webhook pool, retry pool |
| Multi-Tenant Architecture | Isolated data per organization with tenant-aware queries |
| Custom Sending Domains | Per-user Resend domain configuration |
| Per-Recipient Personalization | LangGraph generates individual emails per recipient |
| A/B Testing | Multiple email_template variants per step with split routing |

---

## Quick Reference — Implementation Order for Cursor

### Backend (`backend/` — uv)

```bash
cd backend && uv sync
```

```
1.  pyproject.toml + uv sync     → Dependencies locked with uv
2.  app/core/config.py         → Environment variables + settings
3.  app/core/database.py       → MongoDB Motor client + indexes
4.  app/core/security.py       → Clerk JWT middleware
5.  app/models/                → All Pydantic models
6.  app/repositories/          → MongoDB CRUD (no logic)
7.  app/providers/             → LLM + Email abstractions
8.  app/langgraph/state.py     → CampaignState TypedDict
9.  app/agents/                → Individual agent prompts + logic
10. app/langgraph/graph.py     → Wire agents into StateGraph
11. app/services/              → Business logic
12. app/workers/               → Celery tasks
13. app/api/                   → FastAPI route handlers
14. app/main.py                → App factory + router registration
```

### Frontend (`frontend/` — npm/pnpm)

```
1.  Vite + React 19 + TypeScript
2.  MUI theme + AppShell layout
3.  TanStack Query QueryProvider + queryKeys
4.  api/client.ts + auth token from Clerk
5.  Query/mutation hooks per API contract
6.  Pages per Frontend_Screen_Flow.md (MUI only)
```
