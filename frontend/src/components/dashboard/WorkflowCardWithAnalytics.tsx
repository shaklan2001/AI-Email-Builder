import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardContent from "@mui/material/CardContent";
import Divider from "@mui/material/Divider";
import Skeleton from "@mui/material/Skeleton";
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
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        transition: (theme) =>
          theme.transitions.create(["box-shadow", "transform"], {
            duration: theme.transitions.duration.shorter,
          }),
        "&:hover": {
          boxShadow: (theme) => theme.customShadows.z16,
          transform: "translateY(-2px)",
        },
      }}
    >
      <CardActionArea
        onClick={() => navigate(campaignBuilderPath(workflow.id))}
        sx={{ flex: 1, alignItems: "stretch" }}
      >
        <CardContent sx={{ pb: 2 }}>
          <Stack spacing={2}>
            <Stack spacing={0.5}>
              <Typography variant="subtitle1" component="h2" noWrap>
                {workflow.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Created {formatCreatedDate(workflow.createdAt)}
              </Typography>
            </Stack>

            {showAnalytics && isLoading && (
              <Skeleton
                variant="rounded"
                height={72}
                aria-label="Loading analytics"
              />
            )}
            {showAnalytics && !isLoading && !isError && analytics && (
              <WorkflowAnalyticsSummary analytics={analytics} />
            )}
          </Stack>
        </CardContent>
      </CardActionArea>

      <Divider />

      <CardContent sx={{ pt: 2, "&:last-child": { pb: 3 } }}>
        <WorkflowStatusControl
          workflow={workflow}
          trailingActions={<WorkflowDeleteButton workflow={workflow} />}
        />
      </CardContent>
    </Card>
  );
}
