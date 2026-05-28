# High Level Design (HLD)

# AI-Driven Email Workflow Builder

**Version:** MVP v1

---

## 1. System Overview

The system enables users to create sales and marketing email campaigns through conversational AI.

The user interacts with an AI assistant that:

- Collects campaign requirements
- Designs workflow logic
- Generates email content
- Validates recipients
- Refines email drafts
- Builds workflow automation

Once approved, workflows are executed asynchronously through a dedicated **Workflow Execution Engine**.

> **Key architectural decision:** Workflow *creation* (LangGraph / AI) is fully separated from workflow *execution* (Celery / Execution Engine). This allows independent scaling of AI workloads and workflow-processing workloads.

---

## 2. High-Level Architecture

```
┌─────────────────────────────┐
│         React 19 UI         │
│                             │
│  Chat Panel  |  Preview     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         FastAPI API         │
└──────────────┬──────────────┘
               │
     ┌─────────┼──────────┐
     ▼         ▼          ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│   AI    │ │Workflow │ │Analytics │
│ Service │ │ Service │ │ Service  │
└────┬────┘ └────┬────┘ └────┬─────┘
     │           │           │
     ▼           ▼           ▼
┌─────────────────────────────┐
│          MongoDB            │
└─────────────────────────────┘
               ▲
               │
┌─────────────────────────────┐
│         LangGraph           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        LLM Provider         │
│  OpenAI / Claude / Gemini   │
└─────────────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│    Workflow Execution       │
│          Engine             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         Redis Queue         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Celery Workers        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           Resend            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Webhook Processor      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Workflow Engine       │
└─────────────────────────────┘
```

---

## 3. Frontend Layer

**Technology:** React 19, TypeScript, **MUI (Material UI)**, **TanStack Query**, Vite, Clerk SDK

| Concern | Choice |
|---|---|
| UI components | MUI — layout, forms, tables, dialogs, theme |
| Server state | TanStack Query — caching, mutations, invalidation |
| Auth | Clerk React SDK — JWT attached in API client |
| Build | Vite — dev proxy to FastAPI on `:8000` |

### Chat Module

Handles real-time conversation between user and AI.

```
User: I launched a new product.
  AI: Who is your target audience?
User: Startup founders.
```

**Responsibilities:**
- Message streaming
- Conversation history
- AI response rendering

---

### Workflow Preview Module

Displays the generated workflow structure in real time.

```
Email #1
    ↓
Wait 3 Days
    ↓
Reply?
   YES → End
    NO → Follow Up
```

---

### Email Preview Module

Displays generated email content, updating live as the AI produces output:

- Subject Line
- HTML Email
- Plain Text Email

---

### Recipient Upload Module

- CSV Upload support
- Manual entry support
- Inline validation error display

---

## 4. API Layer

**Technology:** Python 3.14 + FastAPI

Acts as the system gateway for all client requests.

**Responsibilities:**

- Authentication validation (Clerk JWT)
- Route requests to appropriate services
- Save and retrieve workflows
- Handle recipient uploads
- Activate/pause workflows
- Serve analytics data

---

## 5. AI Service

This is the **heart of the system** — it transforms conversation into workflow definitions and email campaigns.

**Responsibilities:**

- Conversation orchestration
- Requirement gathering
- Email generation
- Workflow generation
- Regeneration on user request
- Review support

**Why a separate AI Service?**

Isolating AI logic allows future replacement of the LLM provider (OpenAI → Claude → Gemini) without affecting any business logic.

---

## 6. LangGraph Layer

**Purpose:** Orchestrate multiple AI agents in a coordinated pipeline.

| Agent | Responsibility |
|---|---|
| **Supervisor Agent** | Coordinates all agents; determines next action |
| **Campaign Discovery Agent** | Collects business goal, product info, campaign objective |
| **Audience Discovery Agent** | Collects target audience and customer type |
| **Content Strategy Agent** | Collects tone, CTA, and email format preferences |
| **Asset Collection Agent** | Collects images and attachments |
| **Recipient Validation Agent** | Detects invalid emails, duplicates, and missing values |
| **Workflow Designer Agent** | Creates conditional workflow logic |
| **Copywriter Agent** | Generates subject, HTML email, plain text, and follow-ups |
| **Review Agent** | Checks grammar, readability, sales quality, tone consistency |

**Workflow Designer Agent output example:**

```
Email
    ↓
Wait
    ↓
Condition
    ↓
Follow Up
```

---

## 7. Workflow Service

**Purpose:** Store and manage workflow definitions.

**Responsibilities:**

- Create workflow
- Save draft
- Retrieve workflow
- Activate workflow
- Pause workflow

---

## 8. Workflow Execution Engine

**Purpose:** Execute approved workflows step by step.

**Responsibilities:**

- Track workflow state
- Execute current step
- Determine next step
- Evaluate conditions

**Example:**

```
Current Step: Wait 3 Days
    ↓
Timer Completes
    ↓
Resume Workflow
    ↓
Execute Next Step
```

> This engine is intentionally separate from the AI Service. AI *creates* the workflow; the Execution Engine *runs* it. This separation enables independent scaling.

---

## 9. Queue Layer

**Technology:** Redis

**Purpose:** Store asynchronous tasks for background processing.

**Example tasks:**

```
Send Email
Resume Workflow After Wait
Retry Failed Email
```

**Why a queue?**

A workflow can run for days or weeks. Execution cannot occur inside an HTTP request — the queue decouples activation from execution.

---

## 10. Worker Layer

**Technology:** Celery

**Purpose:** Execute queued tasks asynchronously.

**Responsibilities:**

- Send emails via Resend
- Resume delayed workflows
- Retry failed jobs
- Process scheduled actions

Workers scale horizontally — more workers can be added as load increases.

---

## 11. Email Service

**Provider:** Resend

| Capability | Supported |
|---|---|
| Send Email | ✅ |
| Delivery Tracking | ✅ |
| Open Tracking | ✅ |
| Click Tracking | ✅ |
| Reply Tracking | ✅ |

---

## 12. Webhook Processor

**Purpose:** Receive and process events from Resend.

**Inbound events:**

```
Delivered | Opened | Clicked | Replied | Bounced
```

**Responsibilities:**

- Update analytics records
- Trigger workflow condition evaluation
- Resume conditional branches

---

## 13. Analytics Service

**Purpose:** Campaign performance tracking per workflow.

| Metric | Source |
|---|---|
| Sent | Resend webhook |
| Delivered | Resend webhook |
| Opened | Resend webhook |
| Clicked | Resend webhook |
| Replied | Resend webhook |
| Failed | Resend webhook |

---

## 14. Data Storage Layer

**Technology:** MongoDB

| Collection | Description |
|---|---|
| Users | User accounts and identity |
| Conversations | Full AI chat history per session |
| Workflows | Workflow definitions and state |
| Email Templates | AI-generated email content |
| Recipients | CSV uploads and manual entries |
| Workflow Runs | Runtime execution state per recipient |
| Analytics | Aggregated campaign metrics |
| Webhook Events | Raw Resend events for audit/debug |

**Example document structures:**

```json
// Users
{ "userId": "...", "email": "..." }

// Workflows
{ "workflowId": "...", "steps": [...], "state": "active" }
```

---

## 15. Authentication Layer

**Technology:** Clerk

**Responsibilities:**

- Signup & Login
- Session Management
- User Identity

Backend validates **Clerk JWTs** on every protected request.

---

## 16. Failure Handling

**Email Failure Flow:**

```
Send Email
    ↓
  Fail
    ↓
Retry #1 → Retry #2 → Retry #3
                              ↓
                    Dead Letter Queue
```

**Dead Letter Queue stores:**

| Field | Description |
|---|---|
| Workflow ID | Source workflow reference |
| Recipient | Target email address |
| Error | Failure reason |
| Timestamp | Time of final failure |

---

## 17. Observability

### LangSmith
Tracks agent execution, prompt traces, and LLM latency across all AI interactions.

### Application Logs
Tracks workflow execution, email sending, and errors throughout the system.

### Key Metrics

| Metric | Description |
|---|---|
| Workflow Completion Rate | % of workflows that finish successfully |
| Email Delivery Rate | % of emails successfully delivered |
| Queue Latency | Time from task enqueue to execution |
| AI Response Latency | Time for LangGraph to produce output |

---

## 18. Scalability Design

### Current MVP Stack

```
FastAPI + MongoDB + Redis + Celery + Resend
```

Supports all MVP requirements.

### Future Scale

| Upgrade | Purpose |
|---|---|
| Kafka | Event streaming for high-throughput webhook processing |
| Dedicated Workflow Engine Service | Separate deployable service for execution |
| MongoDB Sharding | Horizontal database scaling |
| Multiple Worker Pools | Isolated pools for email, scheduling, and retries |
| Multi-Tenant Architecture | Isolated data per organization |
| Custom Domains | Per-user sending domains |
| Per-Recipient Personalization | AI-generated individual emails |

---

## 19. End-to-End System Flow

```
User
    ↓
Chat with AI
    ↓
LangGraph Collects Requirements
    ↓
Workflow Generated
    ↓
Emails Generated
    ↓
Recipient Validation
    ↓
Live Preview Updated
    ↓
User Reviews
    ↓
User Edits / Regenerates (Optional)
    ↓
User Approves
    ↓
Workflow Saved to MongoDB
    ↓
Workflow Activated
    ↓
Redis Queue
    ↓
Celery Worker
    ↓
Execution Engine
    ↓
Resend
    ↓
Recipient
    ↓
Webhook Event Received
    ↓
Workflow Condition Evaluated
    ↓
Next Step Executed
    ↓
Workflow Completed
```

---

## Key Architecture Decision

> **Workflow creation and workflow execution are intentionally separated.**
>
> LangGraph handles campaign design and content generation.
> The Workflow Execution Engine handles runtime execution.
>
> This separation allows AI workloads and workflow-processing workloads to scale independently.
