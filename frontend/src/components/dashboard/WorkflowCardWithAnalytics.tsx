import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";
import { campaignBuilderPath } from "../../lib/campaign-routes";
import { useAnalytics } from "../../hooks/use-analytics";
import type { WorkflowRecord } from "../../services/workflow.service";
import { WorkflowAnalyticsSummary } from "./WorkflowAnalyticsSummary";
import { WorkflowDeleteButton } from "./WorkflowDeleteButton";
import { WorkflowStatusControl } from "./WorkflowStatusControl";

interface WorkflowCardWithAnalyticsProps {
  workflow: WorkflowRecord;
}

function formatCreatedDate(isoDate: string): string {
  const parsed = new Date(isoDate);
  if (Number.isNaN(parsed.getTime())) {
    return "—";
  }
  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function WorkflowCardWithAnalytics({ workflow }: WorkflowCardWithAnalyticsProps) {
  const navigate = useNavigate();
  const showAnalytics =
    workflow.status === "active" ||
    workflow.status === "paused" ||
    workflow.status === "completed";
  const { data: analytics, isLoading, isError } = useAnalytics(
    workflow.id,
    showAnalytics,
  );

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
      <CardActionArea
        onClick={() => navigate(campaignBuilderPath(workflow.id))}
        sx={{ height: "100%", alignItems: "stretch" }}
      >
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6" component="h2" noWrap>
              {workflow.name}
            </Typography>

            <WorkflowStatusControl workflow={workflow} />

            <WorkflowDeleteButton workflow={workflow} />

            <Typography variant="body2" color="text.secondary">
              Created {formatCreatedDate(workflow.createdAt)}
            </Typography>

            {showAnalytics && isLoading && (
              <CircularProgress size={16} aria-label="Loading analytics" />
            )}
            {showAnalytics && !isLoading && !isError && analytics && (
              <WorkflowAnalyticsSummary analytics={analytics} />
            )}
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
