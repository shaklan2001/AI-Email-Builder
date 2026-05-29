# 24-langsmith-observability.md

Integrate LangSmith for AI observability.

## Design

Track:

- Agent execution
- Prompt chains
- State transitions
- Token usage
- Latency

## Implementation

Connect LangSmith.

Instrument:

- LangGraph
- LLM calls
- Workflow generation
- Email generation

Add environment variable:

LANGSMITH_API_KEY

Enable tracing.

## Check When Done

- Traces appear in LangSmith
- Agent runs visible
- Prompt chains visible
- Token usage visible
- No runtime errors