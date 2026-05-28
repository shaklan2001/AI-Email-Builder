The workflow builder currently assumes a fixed 3-day follow-up.

This must become configurable.

## Requirements

During campaign creation the AI should ask:

"If a recipient does not reply, when should I send the follow-up?"

Supported values:

- Hours
- Days
- Weeks

Examples:

- 4 Hours
- 1 Day
- 3 Days
- 7 Days
- 2 Weeks

Store in workflow draft:

{
  "follow_up_delay": {
    "value": 3,
    "unit": "days"
  }
}

## Workflow Preview

Display:

Send Initial Email
↓
Wait 3 Days
↓
Reply?

Do not hardcode 3 days anywhere.

## Check When Done

- AI asks follow-up timing
- Workflow stores timing
- Preview reflects timing