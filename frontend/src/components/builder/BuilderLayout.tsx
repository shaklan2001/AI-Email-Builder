import Box from "@mui/material/Box";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { workflowDefinitionToState } from "../../lib/workflow-definition-to-state";
import {
  clearWorkflowDraft,
  sanitizeChatMessages,
  saveWorkflowDraft,
} from "../../lib/workflow-persistence";
import { mockChatMessages } from "../../mocks/chat-messages";
import {
  getRecipientCounts,
  getStoredRecipients,
  resetRecipientCounts,
} from "../../mocks/recipient-storage";
import type { BriefStatus, CampaignBrief } from "../../types/campaign-brief";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import {
  EDIT_DETAILS_MESSAGE,
  LOOKS_GOOD_MESSAGE,
} from "./campaign-brief-panel";
import type { CampaignMetadata, DraftSaveStatus } from "../../types/workflow-draft";
import { defaultWorkflowState } from "../../types/workflow-state";
import type { RecipientCounts } from "../../types/recipient";
import { ChatPanel } from "../chat/chat-panel";
import type { ChatMessage } from "../chat/types";
import { RecipientManagement } from "../recipients/recipient-management";
import { DraftStatusBar } from "./draft-status-bar";
import { PreviewPanel } from "./PreviewPanel";

const AUTO_SAVE_DEBOUNCE_MS = 400;

interface BuilderLayoutProps {
  workflowId: string;
  initialMessages?: ChatMessage[];
  initialWorkflowDefinition?: WorkflowDefinition | null;
  initialCampaignBrief?: CampaignBrief | null;
  initialBriefStatus?: BriefStatus;
  startAtPromptOnClear?: boolean;
  campaign: CampaignMetadata;
  onCampaignChange?: (campaign: CampaignMetadata) => void;
  onDraftCleared?: () => void;
  layoutKey?: number;
}

export function BuilderLayout({
  workflowId,
  initialMessages,
  initialWorkflowDefinition = null,
  initialCampaignBrief = null,
  initialBriefStatus = null,
  startAtPromptOnClear = false,
  campaign,
  onCampaignChange,
  onDraftCleared,
  layoutKey = 0,
}: BuilderLayoutProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    sanitizeChatMessages(initialMessages ?? mockChatMessages),
  );
  const [recipientCounts, setRecipientCounts] = useState<RecipientCounts>(() =>
    getRecipientCounts(workflowId),
  );
  const [saveStatus, setSaveStatus] = useState<DraftSaveStatus>("idle");
  const [apiWorkflow, setApiWorkflow] = useState<WorkflowDefinition | null>(
    initialWorkflowDefinition,
  );
  const [campaignBrief, setCampaignBrief] = useState<CampaignBrief | null>(
    initialCampaignBrief,
  );
  const [briefStatus, setBriefStatus] = useState<BriefStatus>(initialBriefStatus);
  const [chatPending, setChatPending] = useState(false);
  const autoSaveReady = useRef(false);

  const sendBriefActionRef = useRef<((message: string) => void) | null>(null);

  const handleCampaignBriefChange = useCallback(
    (brief: CampaignBrief | null, status: BriefStatus) => {
      setCampaignBrief(brief);
      setBriefStatus(status);
    },
    [],
  );

  const handleBriefApprove = useCallback(() => {
    sendBriefActionRef.current?.(LOOKS_GOOD_MESSAGE);
  }, []);

  const handleBriefEdit = useCallback(() => {
    sendBriefActionRef.current?.(EDIT_DETAILS_MESSAGE);
  }, []);

  const workflow = useMemo(
    () =>
      apiWorkflow
        ? workflowDefinitionToState(apiWorkflow)
        : defaultWorkflowState,
    [apiWorkflow],
  );

  const persistDraft = useCallback(() => {
    saveWorkflowDraft({
      workflowId,
      workflow,
      workflowDefinition: apiWorkflow,
      messages,
      campaign,
      recipients: getStoredRecipients(workflowId),
      invalidRecipientCount: recipientCounts.invalidCount,
      campaignBrief,
      briefStatus,
    });
    setSaveStatus("saved");
  }, [
    workflowId,
    workflow,
    apiWorkflow,
    messages,
    campaign,
    recipientCounts.invalidCount,
    campaignBrief,
    briefStatus,
  ]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      autoSaveReady.current = true;
    }, 0);
    return () => window.clearTimeout(timer);
  }, [layoutKey]);

  useEffect(() => {
    if (!autoSaveReady.current) {
      return;
    }

    setSaveStatus("saving");
    const timer = window.setTimeout(() => {
      persistDraft();
    }, AUTO_SAVE_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
  }, [persistDraft, layoutKey]);

  const handleRecipientsChange = useCallback(() => {
    setRecipientCounts(getRecipientCounts(workflowId));
  }, [workflowId]);

  const handleClearDraft = useCallback(() => {
    clearWorkflowDraft(workflowId);
    resetRecipientCounts(workflowId);
    setMessages(mockChatMessages);
    setApiWorkflow(null);
    setCampaignBrief(null);
    setBriefStatus(null);
    setRecipientCounts({ validCount: 0, invalidCount: 0 });
    setSaveStatus("idle");
    autoSaveReady.current = false;
    onCampaignChange?.({
      firstPrompt: null,
      builderStage: startAtPromptOnClear ? "prompt" : "builder",
    });
    onDraftCleared?.();
    window.setTimeout(() => {
      autoSaveReady.current = true;
    }, 0);
  }, [workflowId, onCampaignChange, onDraftCleared]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: "calc(100vh - 56px)",
        overflow: "hidden",
      }}
    >
      <DraftStatusBar saveStatus={saveStatus} onClearDraft={handleClearDraft} />

      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", md: "row" },
          flex: 1,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            flex: { xs: "1 1 auto", md: "0 0 40%" },
            minHeight: { xs: "45vh", md: 0 },
            minWidth: 0,
          }}
        >
          <ChatPanel
            workflowId={workflowId}
            messages={messages}
            onMessagesChange={setMessages}
            onWorkflowChange={setApiWorkflow}
            onCampaignBriefChange={handleCampaignBriefChange}
            onBriefActionReady={(sendAction) => {
              sendBriefActionRef.current = sendAction;
            }}
            onChatPendingChange={setChatPending}
          />
        </Box>

        <Box
          sx={{
            flex: { xs: "1 1 auto", md: "1 1 60%" },
            minHeight: { xs: "45vh", md: 0 },
            minWidth: 0,
          }}
        >
          <PreviewPanel
            workflowId={workflowId}
            workflowDefinition={apiWorkflow}
            campaignBrief={campaignBrief}
            briefStatus={briefStatus}
            onBriefApprove={handleBriefApprove}
            onBriefEdit={handleBriefEdit}
            briefActionsDisabled={chatPending}
            onWorkflowChange={setApiWorkflow}
          />
        </Box>
      </Box>

      <RecipientManagement
        workflowId={workflowId}
        counts={recipientCounts}
        onCountsChange={handleRecipientsChange}
      />
    </Box>
  );
}
