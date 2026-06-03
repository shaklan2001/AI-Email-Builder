import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { MockWorkflow, WorkflowStatus } from "../../mocks/workflows";

const statusLabels: Record<WorkflowStatus, string> = {
  draft: "Draft",
  generating: "Generating",
  awaiting_approval: "Awaiting Approval",
  active: "Active",
  paused: "Paused",
  completed: "Completed",
};

const statusColors: Record<
  WorkflowStatus,
  "default" | "primary" | "success" | "warning" | "info"
> = {
  draft: "default",
  generating: "info",
  awaiting_approval: "warning",
  active: "success",
  paused: "default",
  completed: "success",
};

interface WorkflowCardProps {
  workflow: MockWorkflow;
}

function formatCreatedDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  return (
    <Card
      variant="outlined"
      sx={{
        height: "100%",
        transition: "border-color 0.2s ease",
        "&:hover": {
          borderColor: "primary.main",
        },
      }}
    >
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="h6" component="h2" noWrap>
            {workflow.name}
          </Typography>

          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography variant="caption" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={statusLabels[workflow.status]}
              color={statusColors[workflow.status]}
              size="small"
            />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Created {formatCreatedDate(workflow.createdAt)}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}
