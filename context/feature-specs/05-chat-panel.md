Implement the AI chat experience.

Do not connect to backend yet.

Use local mock messages.

## Design

ChatGPT-style interface.

Support:

- User messages
- Assistant messages

Input stays fixed at bottom.

Messages scroll independently.

## Implementation

Create reusable:

components/chat/chat-panel.tsx

Support:

- Message list
- User message
- Assistant message
- Input box
- Send button

Use local state only.

No API calls.

## Check When Done

- Messages render correctly
- User can send messages
- Auto-scroll works
- No TypeScript errors