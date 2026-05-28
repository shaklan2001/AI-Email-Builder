# Sequence Diagrams

# AI-Driven Email Workflow Builder

**Version:** MVP v1
**Purpose:** Implementation reference for coding agent — defines exact call order, data flow, storage operations, and API contracts across all major system flows.

---

## System Components Reference

| Component | Technology | Role |
|---|---|---|
| React UI | React 19 + TypeScript + MUI + TanStack Query | Frontend client |
| FastAPI | Python 3.14 + FastAPI | API gateway |
| AI Service | Internal service | LangGraph orchestration wrapper |
| LangGraph | LangGraph | Multi-agent orchestration |
| LLM | OpenAI / Claude / Gemini | Language model |
| Workflow Service | Internal service | Workflow CRUD |
| Workflow Engine | Internal service | Step execution logic |
| Recipient Service | Internal service | CSV parsing + validation |
| Analytics Service | Internal service | Metrics aggregation |
| Webhook Processor | Internal service | Resend event handler |
| MongoDB | MongoDB | Persistent storage |
| Redis | Redis | Task queue |
| Celery Worker | Celery | Async task executor |
| Resend | Resend API | Email delivery + webhooks |

---

## Sequence Diagram 1 — AI Workflow Creation

### Scenario
User sends their first message describing a campaign.

```
User: "I launched a new air purifier. I want to email 100 customers."
```

### Flow

```
User
 │
 │  (1) Send message
 ▼
React UI
 │
 │  POST /chat
 │  Body: { conversation_id, message }
 ▼
FastAPI
 │
 │  (2) Validate Clerk JWT
 │  (3) Route to AI Service
 ▼
AI Service
 │
 │  (4) Load conversation history from MongoDB
 │  (5) Build LangGraph input state
 ▼
LangGraph Supervisor
 │
 ├── (6a) Campaign Discovery Agent  → Extracts: business goal, product info
 ├── (6b) Audience Discovery Agent  → Extracts: target audience, segment
 ├── (6c) Content Strategy Agent    → Extracts: tone, CTA, email format
 └── (6d) Workflow Designer Agent   → Builds: workflow step definitions
 │
 │  (7) Call LLM with agent prompt
 ▼
LLM
 │
 │  (8) Return generated response
 ▼
AI Service
 │
 │  (9) Parse LLM output
 │  (10) Update workflow draft
 ▼
MongoDB
 │  UPSERT conversations
 │  UPSERT workflows (draft state)
 │
 │  (11) Return updated conversation + workflow draft
 ▼
FastAPI
 │
 │  (12) Stream response to client
 ▼
React UI
 │
 │  (13) Render AI message in chat panel
 │  (14) Update live workflow preview
 ▼
User
```

### MongoDB Write — Conversation

```json
{
  "conversation_id": "conv_123",
  "user_id": "user_456",
  "messages": [
    { "role": "user", "content": "I launched a new air purifier..." },
    { "role": "assistant", "content": "Who is your target audience?" }
  ],
  "workflow_draft": {
    "steps": [],
    "status": "collecting_requirements"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:01:00Z"
}
```

### API Contract

```
POST /chat

Request:
{
  "conversation_id": "conv_123",   // null on first message
  "message": "I launched a new air purifier..."
}

Response:
{
  "conversation_id": "conv_123",
  "reply": "Who is your target audience?",
  "workflow_draft": { ... },
  "status": "collecting_requirements"
}
```

---

## Sequence Diagram 2 — Recipient Upload & Validation

### Scenario
User uploads a CSV file containing recipient data.

### Flow

```
User
 │
 │  (1) Upload CSV file
 ▼
React UI
 │
 │  POST /recipients/upload
 │  Body: multipart/form-data (CSV file + workflow_id)
 ▼
FastAPI
 │
 │  (2) Validate Clerk JWT
 │  (3) Parse CSV file
 ▼
Recipient Service
 │
 ▼
Validation Engine
 │
 ├── (4a) Invalid Email Format Check   → regex validation
 ├── (4b) Duplicate Email Check        → dedup within upload
 └── (4c) Empty Row / Missing Field Check
 │
 │  (5) Separate valid and invalid rows
 ▼
MongoDB
 │  INSERT recipients (valid rows only, status: "pending")
 │  INSERT validation_report
 │
 │  (6) Return validation result
 ▼
FastAPI
 │
 │  (7) Return summary to client
 ▼
React UI
 │
 │  (8) Display validation summary
 │
 │  Example:
 │    100 uploaded
 │     95 valid
 │      5 invalid → show invalid rows
 │
 │  (9) User selects action:
 │      [Continue with 95] [Fix & Re-upload] [Cancel]
 ▼
User
```

### MongoDB Write — Recipients

```json
{
  "recipient_id": "rec_789",
  "workflow_id": "wf_123",
  "user_id": "user_456",
  "email": "john@company.com",
  "name": "John",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### API Contract

```
POST /recipients/upload

Request:
  multipart/form-data
  - file: CSV
  - workflow_id: "wf_123"

Response:
{
  "total": 100,
  "valid": 95,
  "invalid": 5,
  "invalid_rows": [
    { "row": 12, "email": "bademail", "reason": "invalid_format" },
    { "row": 34, "email": "", "reason": "missing_email" }
  ],
  "recipient_batch_id": "batch_001"
}
```

---

## Sequence Diagram 3 — Email Generation

### Scenario
AI has gathered enough information and generates the email content.

### Flow

```
User
 │
 │  (1) Trigger: "Generate email"
 │      (either explicit or automatic after requirement gathering)
 ▼
React UI
 │
 │  POST /chat  (or internal trigger from AI Service)
 ▼
FastAPI
 │
 ▼
AI Service
 │
 │  (2) Load conversation state from MongoDB
 │  (3) Build Copywriter Agent prompt with collected requirements
 ▼
LangGraph
 │
 ▼
Copywriter Agent
 │
 │  (4) Call LLM with full context
 ▼
LLM
 │
 │  (5) Return generated email draft
 ▼
Review Agent
 │
 │  (6) Validate:
 │       - Grammar
 │       - Tone consistency
 │       - Readability
 │       - Sales quality
 │
 │  (7) Return reviewed + approved email
 ▼
AI Service
 │
 │  (8) Parse email output
 ▼
MongoDB
 │  INSERT email_templates
 │  UPDATE workflow_draft with template reference
 │
 │  (9) Return generated email content
 ▼
FastAPI
 │
 ▼
React UI
 │
 │  (10) Render email preview in right panel:
 │        - Subject
 │        - HTML preview
 │        - Plain text preview
 ▼
User
```

### MongoDB Write — Email Template

```json
{
  "template_id": "tmpl_001",
  "workflow_id": "wf_123",
  "version": 1,
  "subject": "Breathe clean air with our new purifier",
  "html": "<html>...</html>",
  "text": "Plain text version...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### API Contract

```
Response from POST /chat (during generation phase):
{
  "conversation_id": "conv_123",
  "reply": "Here is your generated email...",
  "email_preview": {
    "subject": "Breathe clean air with our new purifier",
    "html": "<html>...</html>",
    "text": "Plain text version..."
  },
  "template_id": "tmpl_001"
}
```

---

## Sequence Diagram 4 — User Review & Regeneration

### Scenario
User reviews the generated email and requests a revision.

```
User: "Make it more professional"
```

### Flow

```
User
 │
 │  (1) Send refinement instruction
 ▼
React UI
 │
 │  POST /chat
 │  Body: { conversation_id, message: "Make it more professional" }
 ▼
FastAPI
 │
 ▼
AI Service
 │
 │  (2) Load existing email template from MongoDB
 │  (3) Append user instruction to conversation history
 │  (4) Build Copywriter Agent prompt with:
 │       - Original email content
 │       - User refinement instruction
 │       - Original requirements context
 ▼
LangGraph
 │
 ▼
Copywriter Agent
 │
 ▼
LLM
 │
 │  (5) Return revised email
 ▼
AI Service
 │
 ▼
MongoDB
 │  INSERT new email_templates version (version: 2)
 │  UPDATE conversation messages
 │
 │  (6) Return revised email
 ▼
React UI
 │
 │  (7) Update email preview with new version
 ▼
User
```

> **Implementation Note:** Workflow structure does NOT change during regeneration. Only the email template is updated. Workflow draft remains unchanged.

### Versioning Strategy

```json
// Version 1 (original)
{ "template_id": "tmpl_001", "workflow_id": "wf_123", "version": 1 }

// Version 2 (after "make it more professional")
{ "template_id": "tmpl_001", "workflow_id": "wf_123", "version": 2 }

// Always use latest version at activation
```

---

## Sequence Diagram 5 — Workflow Activation

### Scenario
User has approved the workflow and clicks **Activate**.

### Flow

```
User
 │
 │  (1) Click "Activate Workflow"
 ▼
React UI
 │
 │  POST /workflow/activate
 │  Body: { workflow_id }
 ▼
FastAPI
 │
 │  (2) Validate Clerk JWT
 │  (3) Validate workflow is complete:
 │       - Has email template
 │       - Has recipients
 │       - Has workflow steps
 ▼
Workflow Service
 │
 │  (4) Update workflow status → "active"
 ▼
MongoDB
 │  UPDATE workflows SET status = "active"
 │  INSERT workflow_runs (one per recipient)
 │
 │  (5) Queue execution job
 ▼
Redis Queue
 │  PUSH task: execute_workflow { workflow_id, run_id }
 │
 │  (6) Return success immediately
 ▼
FastAPI
 │
 ▼
React UI
 │
 │  (7) Show "Workflow Active" status
 ▼
User
```

> **Implementation Note:** No email is sent at this point. The workflow is only queued. Actual execution begins when the Celery worker picks up the task.

### MongoDB Write — Workflow Run

```json
{
  "run_id": "run_001",
  "workflow_id": "wf_123",
  "recipient_id": "rec_789",
  "current_step": 0,
  "status": "queued",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### API Contract

```
POST /workflow/activate

Request:
{ "workflow_id": "wf_123" }

Response:
{
  "workflow_id": "wf_123",
  "status": "active",
  "runs_queued": 95,
  "message": "Workflow activated. Emails will begin sending shortly."
}
```

---

## Sequence Diagram 6 — Workflow Execution (Email Step)

### Scenario
Celery worker picks up the execution job and sends the first email.

### Flow

```
Redis Queue
 │
 │  (1) Celery worker polls queue
 ▼
Celery Worker
 │
 ▼
Workflow Engine
 │
 │  (2) Load workflow definition from MongoDB
 │  (3) Load workflow_run state (current_step, recipient)
 ▼
MongoDB
 │
 │  (4) Determine current step → "Send Email"
 │  (5) Load email template (latest version)
 │  (6) Inject personalization variables:
 │       {{first_name}}, {{company_name}}, {{email}}
 ▼
Resend API
 │
 │  (7) Send email
 │
 │  On Success:
 ▼
MongoDB
 │  UPDATE workflow_runs SET:
 │    current_step = next_step
 │    status = "waiting"
 │    last_email_sent_at = now()
 │
 │  (8) Determine next step → "Wait 3 Days"
 ▼
Redis Queue
 │  PUSH delayed task: resume_workflow
 │    eta = now() + 3 days
 │    payload: { workflow_id, run_id }
```

### MongoDB Write — Workflow Run Update

```json
{
  "run_id": "run_001",
  "workflow_id": "wf_123",
  "recipient_id": "rec_789",
  "current_step": 1,
  "status": "waiting",
  "last_email_sent_at": "2024-01-01T00:05:00Z",
  "resume_at": "2024-01-04T00:05:00Z"
}
```

---

## Sequence Diagram 7 — Wait Step Execution

### Scenario
A workflow run is in a "Wait 3 Days" step. The timer completes.

### Flow

```
Redis Delayed Queue
 │
 │  (1) 3 days have passed
 │  (2) Delayed job becomes available
 ▼
Celery Worker
 │
 ▼
Workflow Engine
 │
 │  (3) Load workflow_run state from MongoDB
 │  (4) Confirm current step is "Wait" and timer has elapsed
 │  (5) Advance to next step
 │
 │  Next step options:
 │  ├── Send Email → go to Sequence 6
 │  ├── Condition  → go to Sequence 8
 │  └── End        → mark run complete
```

> **Implementation Note:** No thread sleeps. No API polling. The wait is implemented as a **delayed Celery task** with an `eta` (estimated time of arrival). Redis holds the job until the time comes.

---

## Sequence Diagram 8 — Reply Detection & Condition Evaluation

### Scenario
A recipient replies to the email. The system evaluates the reply condition and routes accordingly.

### Flow

```
Recipient
 │
 │  (1) Replies to email
 ▼
Resend
 │
 │  (2) Detects reply event
 │  (3) Fires webhook
 ▼
POST /webhooks/resend
 │
 ▼
Webhook Processor
 │
 │  (4) Parse webhook payload
 │  (5) Identify event type → "reply"
 │  (6) Extract: recipient email, workflow_id, message_id
 ▼
MongoDB
 │  UPDATE recipients SET reply_received = true
 │  INSERT webhook_events (raw event log)
 │
 │  (7) Find associated workflow_run
 ▼
Workflow Engine
 │
 │  (8) Load workflow_run state
 │  (9) Current step is "Condition: Reply Received?"
 │  (10) Evaluate condition → reply_received = true
 │
 │  Branch:
 ├── YES → Execute YES path (e.g., End workflow)
 └── NO  → (handled by Wait timeout → Follow-Up)
 │
 │  (11) Update workflow_run
 ▼
MongoDB
 │  UPDATE workflow_runs SET:
 │    current_step = yes_branch_step
 │    status = "completed" (if End node)
```

### No-Reply Path (Timeout)

```
Wait timer expires (e.g., 3 days after email sent)
 │
 ▼
Celery Worker
 │
 ▼
Workflow Engine
 │
 │  Check: reply_received = false?
 │
 │  YES (no reply received)
 │
 ▼
Execute NO branch → Send Follow-Up Email
```

### Webhook API Contract

```
POST /webhooks/resend

Headers:
  resend-signature: <webhook_signature>

Body (Resend event payload):
{
  "type": "email.replied",
  "data": {
    "message_id": "msg_abc",
    "to": ["recipient@company.com"],
    "from": "sender@yourdomain.com"
  }
}

Response:
{ "status": "ok" }
```

---

## Sequence Diagram 9 — Analytics Tracking

### Scenario
Resend fires an event (open, click, deliver, bounce). The system records it.

### Flow

```
Resend
 │
 │  (1) Email event fires (delivered / opened / clicked / replied / failed)
 ▼
POST /webhooks/resend
 │
 ▼
Webhook Processor
 │
 │  (2) Parse event type and metadata
 │  (3) Identify: workflow_id, recipient_id, message_id
 ▼
Analytics Service
 │
 │  (4) Upsert analytics record
 ▼
MongoDB
 │  UPSERT analytics:
 │    increment: sent / delivered / opened / clicked / replied / failed
 │
 │  INSERT webhook_events (raw event for audit)
 │
 │  (5) Data available for dashboard
 ▼
GET /analytics?workflow_id=wf_123
 │
 ▼
React Dashboard
```

### MongoDB Write — Analytics

```json
{
  "analytics_id": "anl_001",
  "workflow_id": "wf_123",
  "sent": 95,
  "delivered": 92,
  "opened": 45,
  "clicked": 20,
  "replied": 8,
  "failed": 3,
  "updated_at": "2024-01-04T00:00:00Z"
}
```

### API Contract

```
GET /analytics?workflow_id=wf_123

Response:
{
  "workflow_id": "wf_123",
  "sent": 95,
  "delivered": 92,
  "opened": 45,
  "clicked": 20,
  "replied": 8,
  "failed": 3,
  "open_rate": "48.9%",
  "reply_rate": "8.4%"
}
```

---

## MongoDB Collections Summary

Derived from all sequence diagrams above:

| Collection | Written By | Read By |
|---|---|---|
| `users` | Clerk sync | All services |
| `conversations` | AI Service | AI Service |
| `workflows` | Workflow Service | Workflow Engine, AI Service |
| `workflow_runs` | Workflow Engine | Workflow Engine, Analytics |
| `email_templates` | AI Service | Workflow Engine |
| `recipients` | Recipient Service | Workflow Engine |
| `analytics` | Analytics Service | Dashboard API |
| `webhook_events` | Webhook Processor | Debugging / Audit |

---

## API Endpoints Summary

Derived from all sequence diagrams above:

| Method | Endpoint | Sequence |
|---|---|---|
| `POST` | `/chat` | SD1, SD3, SD4 |
| `POST` | `/recipients/upload` | SD2 |
| `POST` | `/workflow/activate` | SD5 |
| `POST` | `/workflow/pause` | — |
| `GET` | `/analytics` | SD9 |
| `POST` | `/webhooks/resend` | SD8, SD9 |

---

## Celery Task Summary

Derived from all sequence diagrams above:

| Task Name | Triggered By | Sequence |
|---|---|---|
| `execute_workflow` | Workflow activation | SD6 |
| `resume_workflow` | Delayed Redis job (wait step) | SD7 |
| `evaluate_condition` | Webhook processor or timer | SD8 |
| `send_email` | Workflow engine | SD6 |
| `retry_email` | Failed send attempt | SD6 |

---

## Next Step — LLD

These sequence diagrams are now sufficient to begin Low Level Design:

1. **MongoDB Schema Design** — collection schemas derived from writes above
2. **LangGraph State Design** — agent graph and state object
3. **FastAPI Folder Structure** — routers, services, models
4. **API Contracts** — request/response Pydantic models
5. **Celery Task Design** — task signatures and retry config
6. **Webhook Event Models** — Resend payload parsing
