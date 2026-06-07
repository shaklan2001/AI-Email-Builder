import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { clearWorkflowDraft } from "../lib/workflow-persistence";
import { mapQueryResult } from "../lib/map-query-result";
import { resetRecipientCounts } from "../mocks/recipient-storage";
import {
  deleteWorkflow,
  fetchWorkflows,
  type WorkflowRecord,
} from "../services/workflow.service";

export function useWorkflows() {
  const query = useQuery({
    queryKey: queryKeys.workflows,
    queryFn: ({ signal }) => fetchWorkflows({ signal }),
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteWorkflow,
    onSuccess: (_result, workflowId) => {
      clearWorkflowDraft(workflowId);
      resetRecipientCounts(workflowId);
      queryClient.setQueryData<WorkflowRecord[]>(queryKeys.workflows, (current) =>
        (current ?? []).filter((workflow) => workflow.id !== workflowId),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
      queryClient.removeQueries({ queryKey: queryKeys.workflow(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.workflowSession(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.analytics(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.chatThread(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.campaignBrief(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.workflowPreview(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.generatedEmails(workflowId) });
      queryClient.removeQueries({ queryKey: queryKeys.conversationThreads(workflowId) });
      queryClient.removeQueries({
        queryKey: queryKeys.conversationThreadPreview(workflowId),
      });
    },
  });
}
