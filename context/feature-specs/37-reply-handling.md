# Reply handling

Process inbound email replies from Resend webhooks through classification and lead updates.

## Flow

```
Webhook (email.received → replied)
  → MongoDB (webhook_events)
  → LangGraph (classify_intent)
  → Reply intent (LLM + keyword fallback)
  → MongoDB (inbound_replies + leads)
```

Runs alongside existing workflow condition evaluation on `replied` events.

After classification, runs agent tools (`44-agent-tools-system.md`) and returns `tool_called`, `selected_tool`, `agent_response` on the webhook result.

## Intent classifications

| Intent | Lead status |
|--------|-------------|
| `interested` | `interested` |
| `not_interested` | `not_interested` |
| `need_more_info` | `replied` |
| `book_demo` | `booked_demo` |

## Backend

- `app/schemas/reply_intent.py` — `ReplyIntent` enum
- `app/agents/reply_intent_agent.py` — Groq classification with keyword fallback
- `app/langgraph/reply_graph.py` — single-node graph
- `app/services/reply_handling_service.py` — orchestration
- `app/repositories/inbound_reply_repository.py` — `inbound_replies`
- `app/repositories/lead_repository.py` — `leads` upsert by `workflow_id` + `email`
- `app/services/webhook_processing_service.py` — invokes reply handler on `replied`

## Webhook result fields

- `reply_classified` — intent assigned
- `reply_intent` — classified value
- `lead_updated` — lead upserted

## Indexes

- `leads`: unique `(workflow_id, email)`
- `inbound_replies`: `(workflow_id, created_at)`

## Check when done

- [x] Reply classified into one of four intents
- [x] Lead status updated automatically
- [x] Inbound reply stored in MongoDB
- [x] Webhook tests assert `reply_classified` and `lead_updated`
