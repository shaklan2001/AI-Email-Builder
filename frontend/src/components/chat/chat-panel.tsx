import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  autoSendKey,
  hasAutoSentChatMessage,
  markAutoSentChatMessage,
} from "../../lib/chat-auto-send";
import { useInvalidateWorkflowQueries } from "../../hooks/use-invalidate-workflow-queries";
import { useSendChatMessage } from "../../hooks/use-send-chat-message";
import { ChatInput } from "./chat-input";
import { MessageList } from "./message-list";
import type { BriefStatus, CampaignBrief } from "../../types/campaign-brief";
import type { ReviewStatus } from "../../types/workflow-review";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import type { ChatMessage } from "./types";

function createMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function withoutLoadingMessages(messages: ChatMessage[]): ChatMessage[] {
  return messages.filter((m) => !m.isLoading);
}

interface ChatPanelProps {
  workflowId: string;
  messages: ChatMessage[];
  onMessagesChange: Dispatch<SetStateAction<ChatMessage[]>>;
  onWorkflowChange?: (workflow: WorkflowDefinition | null) => void;
  onCampaignBriefChange?: (brief: CampaignBrief | null, status: BriefStatus) => void;
  onReviewStateChange?: (status: ReviewStatus, activationAllowed: boolean) => void;
  onBriefActionReady?: (sendAction: (message: string) => void) => void;
  onChatPendingChange?: (pending: boolean) => void;
}

export function ChatPanel({
  workflowId,
  messages,
  onMessagesChange,
  onWorkflowChange,
  onCampaignBriefChange,
  onReviewStateChange,
  onBriefActionReady,
  onChatPendingChange,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const sendInFlightRef = useRef(false);
  const { mutateAsync, isError, error, reset, variables } = useSendChatMessage();
  const invalidateWorkflowQueries = useInvalidateWorkflowQueries();

  const applyAssistantResponse = useCallback(
    (data: {
      message: string;
      workflowPreview: WorkflowDefinition | null;
      campaignBrief: CampaignBrief | null;
      briefStatus: BriefStatus;
      reviewStatus: ReviewStatus;
      activationAllowed: boolean;
    }) => {
      const assistantMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: data.message,
      };
      onMessagesChange((prev) => [...withoutLoadingMessages(prev), assistantMessage]);
      if (data.workflowPreview) {
        onWorkflowChange?.(data.workflowPreview);
      }
      onCampaignBriefChange?.(data.campaignBrief, data.briefStatus);
      onReviewStateChange?.(data.reviewStatus, data.activationAllowed);
    },
    [onCampaignBriefChange, onMessagesChange, onReviewStateChange, onWorkflowChange],
  );

  const sendToApi = useCallback(
    async (message: string) => {
      if (sendInFlightRef.current) {
        return;
      }
      sendInFlightRef.current = true;
      setIsSending(true);

      const loadingMessage: ChatMessage = {
        id: createMessageId(),
        role: "assistant",
        content: "",
        isLoading: true,
      };
      onMessagesChange((prev) => [...withoutLoadingMessages(prev), loadingMessage]);

      try {
        const data = await mutateAsync({ message, threadId: workflowId });
        applyAssistantResponse(data);
        invalidateWorkflowQueries(workflowId);
      } catch {
        onMessagesChange((prev) => withoutLoadingMessages(prev));
      } finally {
        sendInFlightRef.current = false;
        setIsSending(false);
      }
    },
    [
      applyAssistantResponse,
      invalidateWorkflowQueries,
      mutateAsync,
      onMessagesChange,
      workflowId,
    ],
  );

  const sendBriefAction = useCallback(
    (actionMessage: string) => {
      if (isSending) {
        return;
      }
      const userMessage: ChatMessage = {
        id: createMessageId(),
        role: "user",
        content: actionMessage,
      };
      onMessagesChange((prev) => [...withoutLoadingMessages(prev), userMessage]);
      void sendToApi(actionMessage);
    },
    [isSending, onMessagesChange, sendToApi],
  );

  useEffect(() => {
    onBriefActionReady?.(sendBriefAction);
  }, [onBriefActionReady, sendBriefAction]);

  useEffect(() => {
    onChatPendingChange?.(isSending);
  }, [isSending, onChatPendingChange]);

  useEffect(() => {
    if (isSending) {
      return;
    }

    let lastUserIndex = -1;
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === "user") {
        lastUserIndex = i;
        break;
      }
    }
    if (lastUserIndex < 0) {
      return;
    }

    const hasAssistantAfterUser = messages
      .slice(lastUserIndex + 1)
      .some((m) => m.role === "assistant" && !m.isLoading);

    if (hasAssistantAfterUser) {
      return;
    }

    const userMessage = messages[lastUserIndex];
    if (!userMessage.content.trim()) {
      return;
    }

    const key = autoSendKey(workflowId, userMessage.id);
    if (hasAutoSentChatMessage(key)) {
      return;
    }

    markAutoSentChatMessage(key);
    void sendToApi(userMessage.content.trim());
  }, [messages, isSending, sendToApi, workflowId]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmed,
    };

    onMessagesChange((prev) => [...withoutLoadingMessages(prev), userMessage]);
    setInput("");
    void sendToApi(trimmed);
  }, [input, isSending, onMessagesChange, sendToApi]);

  const handleRetry = useCallback(() => {
    if (!variables) {
      return;
    }
    reset();
    void sendToApi(variables.message);
  }, [reset, sendToApi, variables]);

  return (
    <Paper
      variant="outlined"
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        borderRadius: 0,
        borderTop: 0,
        borderBottom: 0,
        borderLeft: 0,
      }}
    >
      <Box sx={{ px: 2, py: 1.5, flexShrink: 0 }}>
        <Typography variant="h6" component="h2">
          AI Chat
        </Typography>
      </Box>

      <Divider />

      {isError && (
        <Alert
          severity="error"
          sx={{ mx: 2, mt: 1, flexShrink: 0 }}
          action={
            <Button color="inherit" size="small" onClick={handleRetry}>
              Retry
            </Button>
          }
        >
          {error?.message ?? "Failed to send message. Please try again."}
        </Alert>
      )}

      <MessageList messages={messages} />

      <Divider />

      <Box sx={{ p: 2, flexShrink: 0 }}>
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          disabled={isSending}
        />
      </Box>
    </Paper>
  );
}
