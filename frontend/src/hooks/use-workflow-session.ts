import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { fetchWorkflowSession } from "../services/workflow.service";

export function useWorkflowSession(workflowId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflowSession(workflowId ?? ""),
    queryFn: () => fetchWorkflowSession(workflowId!),
    enabled: Boolean(workflowId) && workflowId !== "new" && enabled,
  });
}
