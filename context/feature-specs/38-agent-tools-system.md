# Agent tools system

LangGraph-powered tool routing for AI reply handling on inbound prospect messages.

## Tools

| Tool | ID | When to use |
|------|-----|-------------|
| Company Knowledge Tool | `company_knowledge` | Product/company questions — e.g. "Tell me more about ZyLabs" |
| Calendar Booking Tool | `calendar_booking` | Demo/scheduling — e.g. "Book a demo next week" |

The LLM (`tool_router_agent`) selects a tool; keyword fallback applies when the LLM is unavailable.

## Flow

```
Prospect reply
  → LangGraph: select_tool → execute_tool
  → tool_executions (MongoDB)
  → agent_response (tool summary returned)
```

Integrated into `reply_handling_service` after inbound reply storage.

## Backend

- `app/tools/company_knowledge.py`, `calendar_booking.py`, `registry.py`
- `app/agents/tool_router_agent.py`
- `app/langgraph/agent_tools_graph.py`
- `app/services/agent_tools_service.py`
- `app/repositories/tool_execution_repository.py` — `tool_executions`
- `POST /api/v1/workflows/{id}/agent-tools/run` — manual/test run
- `GET /api/v1/workflows/{id}/agent-tools/history` — execution history

## Config

- `CALENDAR_BOOKING_URL` (default `https://cal.com/demo`) — booking link base

## Webhook fields

On `replied`: `tool_called`, `selected_tool`, `agent_response`

## Check when done

- [x] Tool calling works (router + execute nodes)
- [x] Tool results returned (`tool_result`, `agent_response`)
- [x] Execution history stored in MongoDB
