# 34-campaign-collection-agent.md

Production LangGraph agent for campaign discovery and brief readiness.

Complements `25-optional-fields-and-skip-handling.md` (policy) and `28-campaign-brief-v2.md` (brief fields).

## Purpose

Collect campaign information through chat without repeating questions or blocking on optional fields.

## Flow position

```
User prompt
  → Campaign collection (this spec)
  → Campaign brief (15.2 / 28)
  → Brief approval
  → Workflow generation (15)
  → Email generation (16)
  → Review (35)
  → Activation (36)
```

## Design

- Extract structured fields from each user message (merge into state; do not wipe prior answers).
- Track `missing_fields` — only required fields block progress.
- Support skip / not sure / recommend for me / anything works via `campaign_field_policy`.
- Ask one focused question at a time when information is missing.
- Require `follow_up_delay` after product/service is known (see `26-follow-up-delay.md`).
- `campaign_name` is optional.

Required for workflow generation: product, audience, CTA, follow-up delay (and brief approval).

## Implementation

**Agent**

- `backend/app/agents/campaign_collection_agent.py` — extract, delegate phrases, `compute_collection_missing_fields()`

**Policy**

- `backend/app/services/campaign_field_policy.py` — skip detection, defaults, minimal product inference

**LangGraph**

- `extract_information` → `missing_information` → `question_generator` | `campaign_brief` | …
- Nodes delegate to collection agent wrappers in `backend/app/langgraph/nodes.py`

**Persistence**

- `missing_fields`, `skipped_fields`, campaign fields on `ConversationState` → MongoDB via `persistence.py`

**Tests**

- `backend/tests/test_campaign_collection_agent.py`
- `backend/tests/test_campaign_field_policy.py`

## Check When Done

- Collection extracts and merges state correctly
- Skip/delegate phrases do not re-ask skipped fields
- `missing_fields` drives next question only
- Follow-up delay collected before brief when product is known
- Campaign brief generated when collection complete
- State persists in MongoDB
- No type errors
