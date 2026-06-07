import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { mapQueryResult } from "../lib/map-query-result";
import { fetchChatThread } from "../services/chat.service";

export function useChatThread(threadId: string | undefined, enabled = true) {
  const query = useQuery({
    queryKey: queryKeys.chatThread(threadId ?? ""),
    queryFn: ({ signal }) => fetchChatThread(threadId!, { signal }),
    enabled: Boolean(threadId) && threadId !== "new" && enabled,
  });

  return {
    ...query,
    ...mapQueryResult(query),
  };
}
