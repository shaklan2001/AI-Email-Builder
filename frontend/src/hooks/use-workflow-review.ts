import { useQuery } from "@tanstack/react-query";
import { mapQueryResult } from "../lib/map-query-result";
import { fetchWorkflowReview } from "../services/review.service";

export function useWorkflowReview(workflowId: string | undefined) {
  const query = useQuery({
    queryKey: ["workflow-review", workflowId],
    queryFn: ({ signal }) => fetchWorkflowReview(workflowId!, { signal }),
    enabled: Boolean(workflowId),
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}
