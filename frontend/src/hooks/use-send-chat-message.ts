import { useMutation } from "@tanstack/react-query";
import {
  sendMessage,
  type SendChatMessageRequest,
  type SendChatMessageResponse,
} from "../services/chat.service";

export function useSendChatMessage() {
  return useMutation<SendChatMessageResponse, Error, SendChatMessageRequest>({
    mutationFn: sendMessage,
  });
}
