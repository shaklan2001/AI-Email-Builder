# 14-groq-llm-integration.md

Integrate a real LLM into the LangGraph workflow.

Use Groq as the LLM provider.

Preferred Models:

- deepseek-r1-distill-llama-70b
OR
- openai/gpt-oss-120b

The model should be configurable through environment variables.

## Design

The AI should act as a sales and marketing campaign strategist.

Responsibilities:

- Understand user intent
- Extract campaign information
- Identify missing information
- Ask intelligent follow-up questions

The AI should not ask all questions at once.

It should ask only the next most relevant question.

Conversation should feel natural and adaptive.

## Implementation

Create:

providers/llm/

- base.py
- groq_provider.py

Create:

LLMProvider interface

Methods:

- generate()
- extract_campaign_data()

Implement:

GroqProvider

Use official Groq SDK.

Create environment variables:

GROQ_API_KEY
GROQ_MODEL

Update LangGraph nodes:

Extract Information Node

Use LLM extraction instead of simple keyword matching.

Question Generator Node

Use LLM to generate the next best follow-up question.

Provide structured output.

Example:

{
  business_goal,
  product_info,
  audience,
  tone,
  cta
}

Use Pydantic models for validation.

Add fallback handling for malformed responses.

## Check When Done

- Groq connection works
- LangGraph uses LLM
- Structured extraction works
- Follow-up questions are intelligent
- State updates correctly
- Errors handled gracefully
- No hardcoded questions
- No type errors