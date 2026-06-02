import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { WorkflowAnalytics } from "../../services/analytics.service";

interface WorkflowAnalyticsSummaryProps {
  analytics: WorkflowAnalytics;
}

const metricLabels: Array<{ key: keyof WorkflowAnalytics; label: string }> = [
  { key: "sent", label: "Sent" },
  { key: "delivered", label: "Delivered" },
  { key: "opened", label: "Opened" },
  { key: "clicked", label: "Clicked" },
  { key: "replied", label: "Replied" },
  { key: "failed", label: "Failed" },
  { key: "bounced", label: "Bounced" },
];

export function WorkflowAnalyticsSummary({ analytics }: WorkflowAnalyticsSummaryProps) {
  const hasActivity = metricLabels.some(({ key }) => analytics[key] > 0);
  if (!hasActivity) {
    return null;
  }

  return (
    <Stack spacing={0.5} component="dl" sx={{ m: 0 }}>
      <Typography variant="caption" color="text.secondary" component="dt">
        Analytics
      </Typography>
      <Stack
        component="dd"
        direction="row"
        flexWrap="wrap"
        gap={1}
        sx={{ m: 0 }}
        aria-label="Workflow engagement metrics"
      >
        {metricLabels.map(({ key, label }) =>
          analytics[key] > 0 ? (
            <Typography key={key} variant="caption" color="text.secondary">
              {label} {analytics[key]}
            </Typography>
          ) : null,
        )}
      </Stack>
    </Stack>
  );
}
