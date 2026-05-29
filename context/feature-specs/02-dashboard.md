Build the workflow dashboard page.

This is the first page users see after authentication.

## Design

Clean SaaS dashboard layout.

Support:

- Empty state
- Existing workflows

Empty state should encourage users to create their first workflow.

No workflow builder functionality yet.

No workflow creation modal yet.

## Implementation

Create:

/dashboard

Layout:

- Page header
- Create Workflow button
- Workflow list section

Workflow Card:

- Workflow Name
- Status
- Created Date

Empty State:

- Icon
- Short description
- Create Workflow CTA

Use mock data for now.

No backend integration.

## Check When Done

- Dashboard route exists
- Empty state works
- Mock workflow cards render
- Responsive layout works
- No TypeScript errors