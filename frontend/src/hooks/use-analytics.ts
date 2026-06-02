import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { fetchWorkflowAnalytics } from "../services/analytics.service";

const REFETCH_INTERVAL_MS = 30_000;

export function useAnalytics(workflowId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.analytics(workflowId ?? ""),
    queryFn: () => fetchWorkflowAnalytics(workflowId!),
    enabled: Boolean(workflowId) && workflowId !== "new" && enabled,
    refetchInterval: REFETCH_INTERVAL_MS,
  });
}
