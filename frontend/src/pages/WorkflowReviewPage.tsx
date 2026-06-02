import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { WorkflowReview } from "../components/review/workflow-review";
import {
  REVIEW_EDIT_CAMPAIGN_MESSAGE,
  REVIEW_REGENERATE_MESSAGE,
} from "../components/builder/workflow-review-panel";
import { queryKeys } from "../api/queryKeys";
import { campaignBuilderPath } from "../lib/campaign-routes";
import { getMockWorkflowReview } from "../mocks/workflow-review";
import {
  approveWorkflowReview,
  fetchWorkflowReview,
} from "../services/review.service";
import { sendMessage } from "../services/chat.service";
import { activateWorkflow } from "../services/workflow.service";

export function WorkflowReviewPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["workflow-review", workflowId],
    queryFn: () => fetchWorkflowReview(workflowId!),
    enabled: Boolean(workflowId),
  });

  const approveMutation = useMutation({
    mutationFn: () => approveWorkflowReview(workflowId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-review", workflowId] });
      queryClient.invalidateQueries({ queryKey: ["chat-thread", workflowId] });
    },
  });

  const activateMutation = useMutation({
    mutationFn: () => activateWorkflow(workflowId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
      void queryClient.invalidateQueries({ queryKey: ["workflow-review", workflowId] });
      navigate("/dashboard", { replace: true });
    },
  });

  const chatAction = useCallback(
    async (message: string) => {
      if (!workflowId) {
        return;
      }
      await sendMessage({ message, threadId: workflowId });
      queryClient.invalidateQueries({ queryKey: ["workflow-review", workflowId] });
      queryClient.invalidateQueries({ queryKey: ["chat-thread", workflowId] });
      navigate(campaignBuilderPath(workflowId));
    },
    [navigate, queryClient, workflowId],
  );

  if (!workflowId) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 3 }}>
        Campaign not found.
      </Typography>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !data) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">
          {error instanceof Error ? error.message : "Could not load workflow review."}
        </Alert>
      </Container>
    );
  }

  const mockExtras = getMockWorkflowReview(workflowId);
  const reviewData = {
    ...data,
    leadStatusCounts: data.leadStatusCounts ?? mockExtras.leadStatusCounts,
    leadDetails: data.leadDetails ?? mockExtras.leadDetails,
  };

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, sm: 4 } }}>
      <Stack spacing={4}>
        <Box>
          <Typography variant="h5" component="h1" gutterBottom>
            Workflow Review
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Approve your workflow before activation. Edit the campaign or regenerate if needed.
          </Typography>
        </Box>

        {!data.activationAllowed && data.reviewStatus !== "approved" && (
          <Alert severity="info">
            Activation is locked until you approve this workflow.
          </Alert>
        )}

        <WorkflowReview
          data={reviewData}
          onLooksGood={() => approveMutation.mutate()}
          onEditCampaign={() => chatAction(REVIEW_EDIT_CAMPAIGN_MESSAGE)}
          onRegenerate={() => chatAction(REVIEW_REGENERATE_MESSAGE)}
          onActivate={
            data.activationAllowed ? () => activateMutation.mutate() : undefined
          }
          actionsDisabled={approveMutation.isPending || activateMutation.isPending}
          approveLoading={approveMutation.isPending}
        />
      </Stack>
    </Container>
  );
}
