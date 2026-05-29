We are changing the workflow creation experience.

Current implementation immediately opens the split-screen builder.

Replace it with a two-stage AI-first workflow creation experience.

## User Flow

Dashboard

↓

Create Workflow

↓

AI Prompt Screen

↓

User submits first prompt

↓

Animated transition

↓

Builder Screen

## Stage 1 — AI Prompt Screen

The workflow creation page should initially look similar to Lovable, Bolt, or v0.

Requirements:

- centered layout
- large heading
- short supporting description
- large prompt input
- primary submit button
- clean SaaS appearance
- no workflow preview visible yet
- no split-screen layout yet

Example copy:

Heading:

"Build Your Email Workflow"

Description:

"Describe your campaign and AI will build the workflow with you."

Placeholder:

"Launch a new product campaign for homeowners..."

The page should feel empty-state focused and encourage users to start the conversation.

## First Prompt Submission

When the user submits the first prompt:

- store the prompt locally
- transition into builder mode

Do not call the backend yet.

Use mock behavior.

## Transition

Animate between:

AI Prompt Screen

↓

Builder Screen

Use a smooth fade and layout transition.

Avoid page reloads.

Avoid route changes.

The experience should feel similar to modern AI builders.

## Stage 2 — Builder Screen

After prompt submission show:

Left Panel:

- AI conversation
- initial user prompt rendered as first message
- empty assistant placeholder

Right Panel:

- Workflow Preview only

Remove:

- Email tab
- Recipients tab

Only show:

Workflow Preview

Use a placeholder workflow representation for now.

Example:

Send Initial Email

↓

Wait 3 Days

↓

Reply?

├─ Yes → Demo Call
└─ No → Follow Up Email

No backend integration.

No AI integration.

No LangGraph integration.

Mock data only.

## Dashboard Fix

The Create Workflow button on the dashboard must navigate correctly to the workflow creation experience.

Current button behavior is not working correctly.

Fix navigation.

## Check When Done

- Create Workflow opens AI prompt screen
- Prompt screen matches AI builder experience
- First prompt transitions into builder mode
- Initial user prompt appears in chat
- Workflow preview appears on right
- Email tab removed
- Recipients tab removed
- No page reloads
- No TypeScript errors
- Build passes