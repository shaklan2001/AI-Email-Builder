import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid2";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { CreateWorkflowButton } from "../components/dashboard/CreateWorkflowButton";
import { DashboardEmptyState } from "../components/dashboard/DashboardEmptyState";
import { WorkflowCard } from "../components/dashboard/WorkflowCard";
import { mockWorkflows } from "../mocks/workflows";

export function DashboardPage() {
  const workflows = mockWorkflows;
  const hasWorkflows = workflows.length > 0;

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, sm: 4 } }}>
      <Stack spacing={4}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems={{ xs: "stretch", sm: "center" }}
          justifyContent="space-between"
        >
          <Box>
            <Typography variant="h5" component="h1" gutterBottom>
              Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage your email workflows in one place.
            </Typography>
          </Box>

          {hasWorkflows && <CreateWorkflowButton />}
        </Stack>

        <Box component="section" aria-label="Workflow list">
          {hasWorkflows ? (
            <Grid container spacing={3}>
              {workflows.map((workflow) => (
                <Grid key={workflow.id} size={{ xs: 12, sm: 6, md: 4 }}>
                  <WorkflowCard workflow={workflow} />
                </Grid>
              ))}
            </Grid>
          ) : (
            <DashboardEmptyState />
          )}
        </Box>
      </Stack>
    </Container>
  );
}
