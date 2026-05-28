# MVP vs Future Scope

# AI-Driven Email Workflow Builder

**Version:** MVP v1  
**Purpose:** Hard boundary for Cursor and human contributors — prevents scope creep during code generation.

---

## MVP (build this)

| # | Capability | Acceptance hint |
|---|---|---|
| 1 | **Conversation-based builder** | User describes campaign; AI gathers requirements via chat |
| 2 | **CSV upload** | `POST /api/recipients/upload` with validation feedback |
| 3 | **Manual recipients** | Add rows in UI without CSV (same validation rules) |
| 4 | **Workflow preview** | Live diagram from `workflow_preview` in chat API |
| 5 | **Email generation** | Subject + HTML + plain text per send step |
| 6 | **Email regeneration** | User instruction → new template version |
| 7 | **Review & approval** | Review screen → explicit activate |
| 8 | **Activation** | Creates `workflow_runs`, enqueues Celery |
| 9 | **Workflow execution** | send → wait → condition → follow-up / end |
| 10 | **Reply detection** | Resend webhook → `reply_received` → condition branch |
| 11 | **Analytics** | sent, delivered, opened, clicked, replied, rates |
| 12 | **Auth** | Clerk login; JWT on API |
| 13 | **Pause workflow** | `POST /api/workflow/pause` |
| 14 | **Provider abstractions** | LLM + email interfaces with Groq + Resend |
| 15 | **Observability** | LangSmith tracing + structured logs |

### MVP user journey (demo script)

```text
Login → Create campaign → Chat with AI → Upload CSV →
Preview workflow + emails → Review → Activate →
View analytics as events arrive
```

---

## NOT MVP (do not build unless explicitly approved)

| Feature | Reason deferred |
|---|---|
| Custom sending domains | Resend domain setup + DNS — ops heavy |
| A/B testing | Requires variant routing + stats model |
| Multi-tenant / organizations | Tenant isolation across all queries |
| CRM integration (HubSpot, Salesforce) | External OAuth + sync pipelines |
| Personalized email per recipient (AI) | N× LLM cost; separate graph path |
| Workflow versioning | Branching history + rollback UI |
| SMS campaigns | Different provider + compliance |
| WhatsApp campaigns | Meta BSP + template approval |
| Slack notifications | Additional channel worker |
| Kafka event bus | Redis sufficient for MVP volume |
| Dedicated workflow microservice | Monolith FastAPI + Celery first |
| Advanced analytics (cohorts, funnels) | Beyond aggregate counters |
| Custom drag-and-drop workflow editor | AI-generated only for MVP |
| Asset CDN / image hosting | URLs or skip in MVP |
| Rate limiting dashboard | Middleware only, no UI |
| Dead letter queue admin UI | Log + Mongo flag sufficient |

---

## Gray area (MVP-lite — allowed if cheap)

| Feature | Guidance |
|---|---|
| Asset collection (links in chat) | Store URLs in state; no upload service |
| Industry pre-fill on create | Single optional form field |
| Email variable injection `{{first_name}}` | Template string replace only — **not** per-recipient AI |
| List workflows on dashboard | `GET /api/workflows` — required for UX |
| Regenerate single step email | One API; no version browser UI |

---

## Implementation guardrails for Cursor

When generating code, **stop** if the change:

- Adds `tenant_id` or `organization_id` to schemas
- Adds A/B `variant` fields to `email_templates`
- Adds CRM SDK imports
- Adds Twilio / WhatsApp / SMS providers
- Adds Kafka producers/consumers
- Generates unique LLM emails per `recipient_id` in a loop
- Builds a node-based workflow canvas (React Flow, etc.)

Instead, link to this file and `ARCHITECTURE_DECISIONS.md`.

---

## MVP success criteria (from PRD)

- [ ] Login
- [ ] Describe campaign through conversation
- [ ] AI gathers requirements
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

---

## Future scope (reference only)

Documented in PRD §19 — implement **after** MVP demo:

- Custom Sending Domains
- Workflow Versioning
- AI Recipient Personalization
- A/B Testing
- CRM Integrations
- SMS / WhatsApp / Slack
- Multi-Tenant Support
- Advanced Campaign Analytics
