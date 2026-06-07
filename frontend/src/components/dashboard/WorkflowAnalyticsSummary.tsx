import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { memo } from "react";
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

export const WorkflowAnalyticsSummary = memo(function WorkflowAnalyticsSummary({
  analytics,
}: WorkflowAnalyticsSummaryProps) {
  const activeMetrics = metricLabels.filter(({ key }) => analytics[key] > 0);
  if (activeMetrics.length === 0) {
    return null;
  }

  return (
    <Stack spacing={1} component="section" aria-label="Workflow engagement metrics">
      <Typography variant="caption" color="text.secondary" fontWeight={600}>
        Analytics
      </Typography>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(72px, 1fr))",
          gap: 1,
          p: 1.5,
          borderRadius: 1.5,
          bgcolor: "background.neutral",
        }}
      >
        {activeMetrics.map(({ key, label }) => (
          <Box key={key} sx={{ textAlign: "center", minWidth: 0 }}>
            <Typography variant="subtitle2" component="p" sx={{ lineHeight: 1.2 }}>
              {analytics[key]}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              {label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Stack>
  );
});
