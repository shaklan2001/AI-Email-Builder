import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { mapQueryResult } from "../lib/map-query-result";
import { fetchWorkflowAnalytics } from "../services/analytics.service";

const REFETCH_INTERVAL_MS = 30_000;

export function useAnalytics(workflowId: string | undefined, enabled = true) {
  const query = useQuery({
    queryKey: queryKeys.analytics(workflowId ?? ""),
    queryFn: ({ signal }) => fetchWorkflowAnalytics(workflowId!, { signal }),
    enabled: Boolean(workflowId) && workflowId !== "new" && enabled,
    refetchInterval: REFETCH_INTERVAL_MS,
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}
