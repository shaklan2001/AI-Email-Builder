# 12-chat-api-integration.md

Connect the frontend chat experience to the backend API.

Do not integrate LangGraph yet.

Do not integrate Groq yet.

The goal is establishing frontend ↔ backend communication.

## Design

The chat panel should send user messages to the backend.

The backend should return mock AI responses.

All communication should happen through the existing FastAPI APIs.

Frontend should no longer generate local mock responses.

## Implementation

Frontend

Replace local assistant simulation.

Create API service:

services/chat.service.ts

Methods:

sendMessage()

POST:

/api/v1/chat/message

Request:

{
message: string,
workflowId: string
}

Response:

{
message: string
}

Use TanStack Query mutation.

Support:

* loading state
* error state
* retry state

Backend

Update:

POST /api/v1/chat/message

Accept message input.

Return mock AI response.

Example:

"Tell me more about your target audience."

No LangGraph yet.

No LLM calls yet.

No database persistence yet.

## Check When Done

* Frontend sends messages to backend
* Backend returns responses
* Messages render correctly
* Loading state works
* Error handling works
* No TypeScript errors
* No backend errors
* Build passes
