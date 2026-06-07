import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { mapQueryResult } from "../lib/map-query-result";
import { fetchConversationThreadPreview } from "../services/conversation-thread.service";

export function useConversationThreadPreview(campaignId: string | undefined) {
  const query = useQuery({
    queryKey: queryKeys.conversationThreadPreview(campaignId ?? ""),
    queryFn: ({ signal }) => fetchConversationThreadPreview(campaignId!, { signal }),
    enabled: Boolean(campaignId),
    staleTime: 30_000,
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}
