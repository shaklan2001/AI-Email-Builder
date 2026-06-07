import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid2";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { CreateWorkflowButton } from "../components/dashboard/CreateWorkflowButton";
import { DashboardEmptyState } from "../components/dashboard/DashboardEmptyState";
import { WorkflowCardWithAnalytics } from "../components/dashboard/WorkflowCardWithAnalytics";
import { QueryState, WorkflowGridSkeleton } from "../components/common";
import { useWorkflows } from "../hooks/use-workflows";

export function DashboardPage() {
  const { data: workflows = [], isLoading, isError, error } = useWorkflows();
  const hasWorkflows = workflows.length > 0;

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, sm: 3 } }}>
      <Stack spacing={4}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems={{ xs: "stretch", sm: "center" }}
          justifyContent="space-between"
        >
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage your AI outreach campaigns in one place.
            </Typography>
          </Box>

          {hasWorkflows && <CreateWorkflowButton />}
        </Stack>

        <Box component="section" aria-label="Campaign list">
          <QueryState
            loading={isLoading}
            isError={isError}
            error={error}
            loadingFallback={<WorkflowGridSkeleton />}
            errorFallbackMessage="Failed to load campaigns."
          >
            {hasWorkflows ? (
              <Grid container spacing={3}>
                {workflows.map((workflow) => (
                  <Grid key={workflow.id} size={{ xs: 12, sm: 6, md: 4 }}>
                    <WorkflowCardWithAnalytics workflow={workflow} />
                  </Grid>
                ))}
              </Grid>
            ) : (
              <DashboardEmptyState />
            )}
          </QueryState>
        </Box>
      </Stack>
    </Container>
  );
}
