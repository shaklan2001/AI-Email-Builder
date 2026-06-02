import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { clearWorkflowDraft } from "../lib/workflow-persistence";
import { deleteWorkflow, fetchWorkflows } from "../services/workflow.service";

export function useWorkflows() {
  return useQuery({
    queryKey: queryKeys.workflows,
    queryFn: fetchWorkflows,
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteWorkflow,
    onSuccess: (_result, workflowId) => {
      clearWorkflowDraft(workflowId);
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
