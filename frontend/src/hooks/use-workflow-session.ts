import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { mapQueryResult } from "../lib/map-query-result";
import { fetchWorkflowSession } from "../services/workflow.service";

export function useWorkflowSession(workflowId: string | undefined, enabled = true) {
  const query = useQuery({
    queryKey: queryKeys.workflowSession(workflowId ?? ""),
    queryFn: ({ signal }) => fetchWorkflowSession(workflowId!, { signal }),
    enabled: Boolean(workflowId) && workflowId !== "new" && enabled,
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}
