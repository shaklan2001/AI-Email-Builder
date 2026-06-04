import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { queryKeys } from "../api/queryKeys";

export function useInvalidateWorkflowQueries() {
  const queryClient = useQueryClient();

  return useCallback(
    (workflowId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflow(workflowId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowSession(workflowId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.campaignBrief(workflowId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowPreview(workflowId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.generatedEmails(workflowId) });
    },
    [queryClient],
  );
}
