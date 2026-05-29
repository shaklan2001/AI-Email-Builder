# 23-analytics.md

Build workflow analytics.

## Design

Track:

- Sent
- Delivered
- Opened
- Clicked
- Replied
- Failed
- Bounced

Analytics should be available per workflow.

## Implementation

Create:

AnalyticsService

Persist event metrics.

Create endpoint:

GET /api/v1/analytics/{workflow_id}

Return:

{
  sent,
  delivered,
  opened,
  clicked,
  replied,
  failed,
  bounced
}

Update metrics from webhook events.

## Check When Done

- Metrics update correctly
- API returns analytics
- Dashboard consumes analytics
- No type errors