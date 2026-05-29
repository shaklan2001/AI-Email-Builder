# 13-langgraph-agent.md

Integrate LangGraph as the conversation orchestration layer.

Do not generate emails yet.

Do not activate workflows yet.

The goal is to allow the AI to collect missing campaign information through structured follow-up questions.

## Design

The AI should behave like a campaign strategist.

It should gather information progressively instead of asking everything at once.

Required information:

- Business Goal
- Product / Service
- Target Audience
- Tone
- CTA

The AI should determine what information is missing and ask the next most relevant question.

The conversation should feel natural and conversational.

## Implementation

Create:

langgraph/

- graph.py
- state.py
- nodes.py

Create CampaignState:

{
  business_goal,
  product_info,
  audience,
  tone,
  cta,
  missing_fields,
  conversation_history
}

Create Nodes:

1. Extract Information Node

Responsibilities:

- analyze latest user message
- extract campaign information
- update state

2. Missing Information Node

Responsibilities:

- determine which required fields are still missing

3. Question Generator Node

Responsibilities:

- generate the next follow-up question

Graph Flow:

START

↓

Extract Information

↓

Check Missing Fields

↓

Generate Next Question

↓

END

Update:

POST /api/v1/chat/message

to invoke LangGraph.

Return:

{
  message: "Who is your target audience?"
}

Store conversation state in memory for now.

No MongoDB persistence yet.

No email generation yet.

No workflow generation yet.

## Check When Done
- LangGraph executes successfully
- State updates correctly
- Missing fields are detected
- AI asks follow-up questions
- API returns LangGraph responses
- No database dependency
- No TypeScript errors
- No backend errors
