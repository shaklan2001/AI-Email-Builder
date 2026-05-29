# 10-workflow-persistence.md

Persist workflow drafts locally.

Users should not lose progress while creating workflows.

## Design

Drafts should save automatically while the user works.

Refreshing the page should restore:

* Chat history
* Workflow preview
* Campaign information
* Recipient information

Users should also be able to manually clear the draft.

No backend integration yet.

Use browser storage only.

## Implementation

Create a workflow persistence layer.

Persist:

* workflow state
* chat messages
* campaign metadata
* recipients

Use localStorage.

Auto-save whenever workflow state changes.

On page load:

* detect existing draft
* restore state automatically

Provide:

* Save Draft status indicator
* Clear Draft action

Handle corrupted draft data gracefully.

## Check When Done

* Refresh restores workflow
* Refresh restores messages
* Refresh restores recipients
* Auto-save works
* Clear Draft works
* No TypeScript errors
* Build passes
