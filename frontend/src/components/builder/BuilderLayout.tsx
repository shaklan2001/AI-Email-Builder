import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearWorkflowDraft,
  sanitizeChatMessages,
  saveRecipientDraft,
} from "../../lib/workflow-persistence";
import { mockChatMessages } from "../../mocks/chat-messages";
import { resetChatThread } from "../../services/chat.service";
import { activateWorkflow } from "../../services/workflow.service";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../api/queryKeys";
import {
  getRecipientCounts,
  getStoredRecipients,
  resetRecipientCounts,
  setStoredRecipients,
} from "../../mocks/recipient-storage";
import {
  fetchWorkflowRecipients,
  saveWorkflowRecipients,
} from "../../services/recipient.service";
import type { BriefStatus, CampaignBrief } from "../../types/campaign-brief";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import {
  EDIT_DETAILS_MESSAGE,
  LOOKS_GOOD_MESSAGE,
} from "./campaign-brief-panel";
import {
  REVIEW_EDIT_CAMPAIGN_MESSAGE,
  REVIEW_LOOKS_GOOD_MESSAGE,
  REVIEW_REGENERATE_MESSAGE,
} from "./workflow-review-panel";
import type { ReviewStatus } from "../../types/workflow-review";
import type { CampaignMetadata, DraftSaveStatus } from "../../types/workflow-draft";
import type { Recipient, RecipientCounts } from "../../types/recipient";
import { ChatPanel } from "../chat/chat-panel";
import type { ChatMessage } from "../chat/types";
import { DraftStatusBar } from "./draft-status-bar";
import { PreviewPanel } from "./PreviewPanel";

const AUTO_SAVE_DEBOUNCE_MS = 400;

interface BuilderLayoutProps {
  workflowId: string;
  initialMessages?: ChatMessage[];
  initialWorkflowDefinition?: WorkflowDefinition | null;
  initialCampaignBrief?: CampaignBrief | null;
  initialBriefStatus?: BriefStatus;
  initialReviewStatus?: ReviewStatus;
  initialActivationAllowed?: boolean;
  startAtPromptOnClear?: boolean;
  campaign?: CampaignMetadata;
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
  initialReviewStatus = null,
  initialActivationAllowed = false,
  startAtPromptOnClear = false,
  onCampaignChange,
  onDraftCleared,
  layoutKey = 0,
}: BuilderLayoutProps) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>(() =>
    sanitizeChatMessages(initialMessages ?? mockChatMessages),
  );
  const [recipients, setRecipients] = useState<Recipient[]>(() =>
    getStoredRecipients(workflowId),
  );
  const [recipientCounts, setRecipientCounts] = useState<RecipientCounts>(() =>
    getRecipientCounts(workflowId),
  );
  const [recipientsSaving, setRecipientsSaving] = useState(false);
  const [recipientSaveError, setRecipientSaveError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<DraftSaveStatus>("idle");
  const [apiWorkflow, setApiWorkflow] = useState<WorkflowDefinition | null>(
    initialWorkflowDefinition,
  );
  const [campaignBrief, setCampaignBrief] = useState<CampaignBrief | null>(
    initialCampaignBrief,
  );
  const [briefStatus, setBriefStatus] = useState<BriefStatus>(initialBriefStatus);
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>(initialReviewStatus);
  const [activationAllowed, setActivationAllowed] = useState(initialActivationAllowed);
  const [workflowStatus, setWorkflowStatus] = useState("draft");
  const [activateError, setActivateError] = useState<string | null>(null);
  const [chatPending, setChatPending] = useState(false);
  const autoSaveReady = useRef(false);
  const queryClient = useQueryClient();

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

  const handleReviewLooksGood = useCallback(() => {
    sendBriefActionRef.current?.(REVIEW_LOOKS_GOOD_MESSAGE);
  }, []);

  const handleReviewEditCampaign = useCallback(() => {
    sendBriefActionRef.current?.(REVIEW_EDIT_CAMPAIGN_MESSAGE);
  }, []);

  const handleReviewRegenerate = useCallback(() => {
    sendBriefActionRef.current?.(REVIEW_REGENERATE_MESSAGE);
  }, []);

  const handleReviewStateChange = useCallback(
    (status: ReviewStatus, allowed: boolean) => {
      setReviewStatus(status);
      setActivationAllowed(allowed);
    },
    [],
  );

  const activateMutation = useMutation({
    mutationFn: () => activateWorkflow(workflowId),
    onSuccess: (result) => {
      setActivateError(null);
      setWorkflowStatus(result.status);
      void queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
      void queryClient.invalidateQueries({ queryKey: queryKeys.chatThread(workflowId) });
      navigate("/dashboard", { replace: true });
    },
    onError: (error: Error) => {
      setActivateError(error.message);
    },
  });

  const handleActivate = useCallback(() => {
    setActivateError(null);
    activateMutation.mutate();
  }, [activateMutation]);

  const persistDraft = useCallback(() => {
    saveRecipientDraft({
      workflowId,
      recipients,
      invalidRecipientCount: recipientCounts.invalidCount,
    });
    setSaveStatus("saved");
  }, [workflowId, recipients, recipientCounts.invalidCount]);

  useEffect(() => {
    setMessages(sanitizeChatMessages(initialMessages ?? mockChatMessages));
    setApiWorkflow(initialWorkflowDefinition);
    setCampaignBrief(initialCampaignBrief);
    setBriefStatus(initialBriefStatus);
    setReviewStatus(initialReviewStatus);
    setActivationAllowed(initialActivationAllowed);
    autoSaveReady.current = false;
    const timer = window.setTimeout(() => {
      autoSaveReady.current = true;
    }, 0);
    return () => window.clearTimeout(timer);
  }, [
    layoutKey,
    workflowId,
    initialMessages,
    initialWorkflowDefinition,
    initialCampaignBrief,
    initialBriefStatus,
    initialReviewStatus,
    initialActivationAllowed,
  ]);

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

  const syncRecipientsLocal = useCallback(
    (nextRecipients: Recipient[], invalidCount: number) => {
      setStoredRecipients(workflowId, nextRecipients, invalidCount);
      setRecipients(nextRecipients);
      setRecipientCounts({
        validCount: nextRecipients.length,
        invalidCount,
      });
    },
    [workflowId],
  );

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const loaded = await fetchWorkflowRecipients(workflowId);
        if (cancelled) {
          return;
        }
        if (loaded.recipients.length > 0) {
          syncRecipientsLocal(loaded.recipients, loaded.counts.invalidCount);
        }
      } catch {
        // Keep local draft/mock counts when API is unavailable.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [workflowId, syncRecipientsLocal]);

  const handleAddRecipientEmails = useCallback(
    async (emails: string[]) => {
      setRecipientsSaving(true);
      setRecipientSaveError(null);
      try {
        const result = await saveWorkflowRecipients(workflowId, emails);
        syncRecipientsLocal(result.recipients, recipientCounts.invalidCount);
        setRecipientCounts({
          validCount: result.counts.validCount,
          invalidCount: recipientCounts.invalidCount,
        });
      } catch (error) {
        setRecipientSaveError(
          error instanceof Error ? error.message : "Could not save recipients.",
        );
        throw error;
      } finally {
        setRecipientsSaving(false);
      }
    },
    [workflowId, syncRecipientsLocal, recipientCounts.invalidCount],
  );

  const handleClearDraft = useCallback(() => {
    void (async () => {
      try {
        await resetChatThread(workflowId);
        await queryClient.invalidateQueries({
          queryKey: queryKeys.chatThread(workflowId),
        });
      } catch {
        // Local clear still runs if API is unavailable.
      }
      clearWorkflowDraft(workflowId);
      resetRecipientCounts(workflowId);
      setRecipients([]);
      setRecipientSaveError(null);
      setMessages(mockChatMessages);
      setApiWorkflow(null);
      setCampaignBrief(null);
      setBriefStatus(null);
      setReviewStatus(null);
      setActivationAllowed(false);
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
    })();
  }, [
    workflowId,
    onCampaignChange,
    onDraftCleared,
    queryClient,
    startAtPromptOnClear,
  ]);

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

      {activateError && (
        <Alert severity="error" sx={{ mx: 2, mt: 1 }} onClose={() => setActivateError(null)}>
          {activateError}
        </Alert>
      )}

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
            onReviewStateChange={handleReviewStateChange}
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
            reviewStatus={reviewStatus}
            activationAllowed={activationAllowed}
            onReviewLooksGood={handleReviewLooksGood}
            onReviewEditCampaign={handleReviewEditCampaign}
            onReviewRegenerate={handleReviewRegenerate}
            onActivate={handleActivate}
            reviewActionsDisabled={chatPending}
            activateLoading={activateMutation.isPending}
            workflowStatus={workflowStatus}
            onWorkflowChange={setApiWorkflow}
            recipientCounts={recipientCounts}
            recipients={recipients}
            onAddRecipientEmails={handleAddRecipientEmails}
            recipientsSaving={recipientsSaving}
            recipientSaveError={recipientSaveError}
            onDismissRecipientError={() => setRecipientSaveError(null)}
          />
        </Box>
      </Box>
    </Box>
  );
}
