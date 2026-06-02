import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { fetchConversationThreadPreview } from "../services/conversation-thread.service";

export function useConversationThreadPreview(campaignId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.conversationThreadPreview(campaignId ?? ""),
    queryFn: () => fetchConversationThreadPreview(campaignId!),
    enabled: Boolean(campaignId),
    staleTime: 30_000,
  });
}
