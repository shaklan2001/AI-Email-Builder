# Product Requirements Document (PRD)

# AI-Driven Email Workflow Builder

**Version:** MVP v1

---

## 1. Product Overview

AI-Driven Email Workflow Builder is a conversational AI platform that enables users to create and execute sales and marketing email campaigns through natural language conversations.

Instead of manually creating workflows using drag-and-drop builders, users interact with an AI assistant that:

- Collects campaign requirements
- Designs workflow logic
- Generates email content
- Validates recipient lists
- Builds follow-up sequences
- Creates reply/no-reply conditions
- Presents a live workflow preview
- Activates workflow execution after approval

The system acts as an **AI Campaign Manager**, **AI Workflow Designer**, and **AI Email Copywriter**.

---

## 2. Problem Statement

Creating sales and marketing email campaigns requires multiple skills:

- Campaign planning
- Audience segmentation
- Email copywriting
- Workflow design
- Follow-up strategy
- Email scheduling
- Analytics tracking

Most users do not have expertise in all these areas.

The goal of this product is to allow users to describe business goals while the AI handles campaign design and workflow creation.

---

## 3. Product Vision

Allow users to launch complete email campaigns through conversation.

| User Focus | AI Handles |
|---|---|
| What they want to achieve | How the campaign should be structured |

**Future vision:** AI becomes a complete campaign strategist capable of building multi-step outreach workflows automatically.

---

## 4. Target Users

**Primary Users:**

- Sales Teams
- Marketing Teams
- Startup Founders
- Business Development Teams
- Product Marketing Teams

**Use Cases:**

- Product Launch Announcements
- Cold Outreach Campaigns
- Lead Nurturing Campaigns
- Follow-Up Sequences
- Demo Booking Campaigns
- Customer Re-engagement Campaigns

---

## 5. Core User Journey

### Step 1 — Login

User logs in using **Clerk Authentication**.

---

### Step 2 — Start Conversation

User initiates a campaign request.

```
User: "I launched a new air purifier and want to email 100 people."
```

---

### Step 3 — AI Requirement Discovery

AI gathers missing information through conversation:

```
AI: What is your business goal?
AI: Who is the audience?
AI: What tone should be used?
AI: Do you want HTML or plain text emails?
AI: Do you have images to include?
AI: Do you have attachments?
AI: What CTA should users take?
AI: What should happen if users reply?
AI: What should happen if users do not reply?
AI: How many days should we wait before follow-up?
```

---

### Step 4 — Live Workflow Draft

AI continuously updates the workflow draft as it collects information.

```
Email #1
    ↓
Wait 3 Days
    ↓
Reply Received?
   YES → End
    NO → Follow-Up Email
              ↓
             End
```

---

### Step 5 — Recipient Collection

Users may provide recipients using:

- CSV Upload
- Manual Entry

---

### Step 6 — Recipient Validation

The system validates uploaded recipients.

**Validation checks:**

- Missing email addresses
- Invalid email format
- Duplicate recipients

**Example:**

```
100 recipients uploaded
 95 valid
  5 invalid
```

**User options:**

- Fix invalid entries
- Skip invalid entries
- Cancel upload

---

### Step 7 — Email Generation

AI generates all email content:

- Subject Line
- HTML Email
- Plain Text Email
- Follow-Up Emails

---

### Step 8 — Live Preview

The application contains two panels updating in real time.

| Left Panel | Right Panel |
|---|---|
| AI Conversation | Workflow Preview + Email Preview |

---

### Step 9 — Review and Refinement

Users may:

- Accept generated content
- Edit content manually
- Ask AI to regenerate content

**Example regeneration requests:**

```
"Make this more professional"
"Shorten the email"
"Add urgency"
"Rewrite CTA"
```

---

### Step 10 — Approval

User confirms:

- ✅ Workflow Logic
- ✅ Recipient List
- ✅ Email Content

---

### Step 11 — Workflow Activation

Workflow becomes active and enters execution automatically.

---

## 6. User Interface

**Frontend stack (MVP):** React 19, TypeScript, **MUI** for UI components, **TanStack Query** for API fetching/caching, Vite, Clerk.

**Backend stack (MVP):** Python, FastAPI, **uv** for package management (`pyproject.toml` + lockfile).

See `docs/LLD_AI_Email_Workflow_Builder.md` and `ARCHITECTURE_DECISIONS.md` (ADR-009–011).

### Left Panel — AI Chat

**Responsibilities:**

- Requirement Collection
- Campaign Planning
- Workflow Design Discussion
- Email Refinement

---

### Right Panel — Live Preview

**Workflow Preview:**

```
Email #1
    ↓
Wait 3 Days
    ↓
Reply?
   YES → Demo Booking
    NO → Follow-Up
```

**Email Preview:**

- Subject Line
- HTML Email
- Plain Text Email
- Follow-Up Emails

Updates in real time as AI generates content.

---

## 7. AI System Design

The AI system is powered by **LangGraph**.

| Agent | Responsibility |
|---|---|
| **Supervisor Agent** | Coordinates all AI agents; determines which runs next |
| **Campaign Discovery Agent** | Collects business goal, campaign objective, product info |
| **Audience Discovery Agent** | Collects target audience, segment, and customer type |
| **Content Strategy Agent** | Collects tone, CTA, messaging style, and email format |
| **Asset Collection Agent** | Collects images, attachments, and marketing assets |
| **Recipient Validation Agent** | Validates CSV uploads, manual entries, and email formatting |
| **Workflow Designer Agent** | Creates workflow logic and branching conditions |
| **Email Copywriter Agent** | Generates subject line, HTML email, plain text, and follow-ups |
| **Review Agent** | Checks grammar, tone consistency, sales quality, and readability |

---

## 8. Workflow Model

Workflow logic is generated automatically by AI. Users do not manually create nodes.

### Supported Node Types

#### Send Email
Sends the AI-generated email to recipients.

#### Wait
User-defined delay before the next step.

```
3 Days | 7 Days | 14 Days
```

#### Condition
Evaluates a condition and branches accordingly.

```
Reply Received?
  YES → Path A
   NO → Path B
```

#### End
Marks workflow completion.

---

## 9. Recipient Management

**CSV Upload:**

```csv
name,email
John,john@company.com
Jane,jane@company.com
```

**Manual Entry:**

```
john@company.com
jane@company.com
```

**Validation:**

- Invalid format detection
- Duplicate detection
- Empty value detection

---

## 10. Email Generation

AI generates:

- Subject Line
- HTML Email
- Plain Text Email

**Optional elements:**

- Image Sections
- CTA Buttons
- Attachments

Users can regenerate content multiple times before approval.

---

## 11. Workflow Execution

```
Workflow Approved
    ↓
Queued
    ↓
Executed
    ↓
Wait Conditions
    ↓
Reply Conditions
    ↓
Follow-Up Execution
    ↓
Completed
```

Execution continues automatically until workflow completion.

---

## 12. Email Delivery

| Property | Detail |
|---|---|
| Provider | Resend |
| Email Delivery | ✅ |
| Delivery Tracking | ✅ |
| Open Tracking | ✅ |
| Click Tracking | ✅ |
| Reply Tracking | ✅ |

---

## 13. Reply Detection

Reply detection uses **Resend Webhooks**.

```
Recipient Reply
    ↓
Webhook Event
    ↓
Workflow Evaluation
    ↓
Conditional Path Execution
```

---

## 14. Analytics

Tracked per workflow via Resend webhooks:

| Metric | Tracked |
|---|---|
| Sent | ✅ |
| Delivered | ✅ |
| Opened | ✅ |
| Clicked | ✅ |
| Replied | ✅ |
| Failed | ✅ |

---

## 15. Workflow States

| State | Description |
|---|---|
| Draft | Being built by AI |
| Generating | AI actively producing content |
| Awaiting Approval | Ready for user review |
| Active | Running and sending emails |
| Paused | Execution stopped, history preserved |
| Completed | All steps finished |
| Archived | No longer in use |

---

## 16. Failure Handling

**Retry Strategy:**

```
Attempt 1 → Attempt 2 → Attempt 3 → Dead Letter Queue
```

- All failed tasks are logged
- Dead Letter Queue stores: Workflow ID, Recipient, Error, Timestamp

---

## 17. Security Requirements

| Concern | Solution |
|---|---|
| Authentication | Clerk |
| Authorization | Users access only their own workflows |
| Validation | Server-side validation for all requests |
| Secrets | Stored securely via environment variables |
| Audit Logging | All workflow actions recorded |

---

## 18. Non-Functional Requirements

| Category | Requirements |
|---|---|
| **Scalability** | Queue-based architecture, horizontal worker scaling |
| **Reliability** | Retry mechanisms, failure recovery |
| **Observability** | LangSmith tracing, workflow monitoring, error tracking |
| **Maintainability** | Modular architecture, provider abstractions |
| **Performance** | Async workflow execution, non-blocking API requests |

---

## 19. Future Scope

- Custom Sending Domains
- Workflow Versioning
- AI Recipient Personalization
- A/B Testing
- CRM Integrations
- SMS Campaigns
- WhatsApp Campaigns
- Slack Notifications
- Multi-Tenant Support
- Advanced Campaign Analytics

---

## 20. MVP Success Criteria

A user should be able to:

- [ ] Login
- [ ] Describe a campaign through conversation
- [ ] Allow AI to gather requirements
- [ ] Upload or enter recipients
- [ ] Validate recipient lists
- [ ] Generate workflow logic automatically
- [ ] Generate email content automatically
- [ ] Review workflow preview
- [ ] Edit or regenerate email content
- [ ] Approve workflow
- [ ] Activate workflow
- [ ] Send emails automatically
- [ ] Execute reply / no-reply flows
- [ ] Track campaign analytics
