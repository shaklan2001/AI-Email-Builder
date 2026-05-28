Implement LangGraph state persistence.

Purpose

Single source of truth for conversation.

Create:

ConversationState

Fields

- messages
- campaign_brief
- workflow
- email_templates
- recipients
- missing_fields
- brief_status / brief_approved
- review_status / regenerate_workflow
- current_stage (derived)

Stages

- discovery
- campaign_brief
- workflow_generation
- email_generation
- review
- activation

Persist state after every message.

State must reload after page refresh.

Fix:

- stale preview bug
- wrong campaign bug
- previous campaign appearing in new chat

Routing

- Post-brief chat does not re-run workflow generation on every message (routes to `question_generator` unless regenerating).
- Regenerate from review sets `regenerate_workflow` → `generate_workflow` path.

Related specs (pipeline order)

- `34-campaign-collection-agent.md` → `15.2` / `28` brief → `15` workflow → `16` emails → `35` review → `36` activation

Check When Done

- state survives refresh
- new chat creates fresh state
- preview resets correctly
- review_status and activation stage behave correctly