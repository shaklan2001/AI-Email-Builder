import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "../api/queryKeys";
import { fetchChatThread } from "../services/chat.service";

export function useChatThread(threadId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.chatThread(threadId ?? ""),
    queryFn: () => fetchChatThread(threadId!),
    enabled: Boolean(threadId) && threadId !== "new" && enabled,
  });
}
