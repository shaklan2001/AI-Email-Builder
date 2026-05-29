Build the AI Workflow Builder layout shell.

No AI functionality yet.

No backend integration yet.

Only create the layout structure.

## Design

Split screen layout.

Left:

- AI Chat Panel

Right:

- Preview Panel

The layout should fill the available viewport.

Resizable panels are optional.

## Implementation

Create:

/workflows/[workflowId]

Layout:

Left Panel:

- Chat header
- Empty message area
- Input area

Right Panel:

Tabs:

- Workflow
- Email
- Recipients

Each tab displays placeholder content.

No real data yet.

## Check When Done

- Builder page exists
- Two-panel layout works
- Tabs switch correctly
- Responsive layout works
- No TypeScript errors