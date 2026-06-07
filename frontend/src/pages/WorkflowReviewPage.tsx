import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { WorkflowReview } from "../components/review/workflow-review";
import {
  REVIEW_EDIT_CAMPAIGN_MESSAGE,
  REVIEW_REGENERATE_MESSAGE,
} from "../components/builder/workflow-review-panel";
import { QueryState, ReviewPageSkeleton } from "../components/common";
import { queryKeys } from "../api/queryKeys";
import { campaignBuilderPath } from "../lib/campaign-routes";
import { useWorkflowReview } from "../hooks/use-workflow-review";
import { getMockWorkflowReview } from "../mocks/workflow-review";
import { approveWorkflowReview } from "../services/review.service";
import { sendMessage } from "../services/chat.service";
import { activateWorkflow } from "../services/workflow.service";

export function WorkflowReviewPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useWorkflowReview(workflowId);

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

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 3 } }}>
      <Stack spacing={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Workflow Review
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Approve your workflow before activation. Edit the campaign or regenerate if needed.
          </Typography>
        </Box>

        <QueryState
          loading={isLoading}
          isError={isError || !data}
          error={error}
          loadingFallback={<ReviewPageSkeleton />}
          errorFallbackMessage="Could not load workflow review."
        >
          {data && (
            <>
              {!data.activationAllowed && data.reviewStatus !== "approved" && (
                <Alert severity="info">
                  Activation is locked until you approve this workflow.
                </Alert>
              )}

              <WorkflowReview
                data={{
                  ...data,
                  leadStatusCounts:
                    data.leadStatusCounts ??
                    getMockWorkflowReview(workflowId).leadStatusCounts,
                  leadDetails:
                    data.leadDetails ?? getMockWorkflowReview(workflowId).leadDetails,
                }}
                onLooksGood={() => approveMutation.mutate()}
                onEditCampaign={() => chatAction(REVIEW_EDIT_CAMPAIGN_MESSAGE)}
                onRegenerate={() => chatAction(REVIEW_REGENERATE_MESSAGE)}
                onActivate={
                  data.activationAllowed ? () => activateMutation.mutate() : undefined
                }
                actionsDisabled={approveMutation.isPending || activateMutation.isPending}
                approveLoading={approveMutation.isPending}
              />
            </>
          )}
        </QueryState>
      </Stack>
    </Container>
  );
}
