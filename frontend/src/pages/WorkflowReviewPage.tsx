import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useParams } from "react-router-dom";
import { WorkflowReview } from "../components/review/workflow-review";
import { getMockWorkflowReview } from "../mocks/workflow-review";

export function WorkflowReviewPage() {
  const { workflowId } = useParams<{ workflowId: string }>();

  if (!workflowId) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 3 }}>
        Workflow not found.
      </Typography>
    );
  }

  const reviewData = getMockWorkflowReview(workflowId);

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 4 } }}>
      <Stack spacing={4}>
        <Box>
          <Typography variant="h5" component="h1" gutterBottom>
            Workflow Review
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Review your workflow details before approval.
          </Typography>
        </Box>

        <WorkflowReview data={reviewData} />
      </Stack>
    </Container>
  );
}
