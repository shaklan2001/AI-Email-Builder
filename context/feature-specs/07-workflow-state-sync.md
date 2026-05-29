Connect the chat panel and workflow preview.

No backend integration.

No AI integration.

No LangGraph integration.

The workflow preview should update based on chat messages.

Use simple keyword detection.

Examples:

"wait 5 days"
→ update wait step

"follow up"
→ create follow up node

"discount"
→ create discount email node

Store workflow state locally.

Chat becomes the source of truth.

Workflow preview updates in real time.

Use React state only.

No API calls.

## Check When Done

- Chat updates workflow
- Workflow re-renders correctly
- State persists while on page
- No TypeScript errors