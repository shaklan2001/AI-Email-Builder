import Box from "@mui/material/Box";
import { mainContentHeight } from "src/layouts/config-layout";
import Fade from "@mui/material/Fade";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { campaignBuilderPath } from "../lib/campaign-routes";
import { AiPromptScreen } from "../components/builder/ai-prompt-screen";
import { BuilderLayout } from "../components/builder/BuilderLayout";
import { BuilderPageSkeleton } from "../components/common";
import type { ChatMessage } from "../components/chat/types";
import { useInvalidateWorkflowQueries } from "../hooks/use-invalidate-workflow-queries";
import { useChatThread } from "../hooks/use-chat-thread";
import { useWorkflowSession } from "../hooks/use-workflow-session";
import { buildBuilderBoot, type BuilderBootState } from "../lib/builder-boot";
import type { BuilderStage, CampaignMetadata } from "../types/workflow-draft";

const TRANSITION_MS = 400;

function createMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function buildInitialChatMessages(firstPrompt: string): ChatMessage[] {
  return [
    {
      id: createMessageId(),
      role: "user",
      content: firstPrompt,
    },
  ];
}

function applyBoot(
  boot: BuilderBootState,
  setters: {
    setStage: (s: BuilderStage) => void;
    setFirstPrompt: (p: string | null) => void;
    setShowPrompt: (v: boolean) => void;
    setShowBuilder: (v: boolean) => void;
    setCampaign: (c: CampaignMetadata) => void;
    setSessionMessages: (m: ChatMessage[] | undefined) => void;
    setLayoutKey: (fn: (k: number) => number) => void;
  },
) {
  setters.setStage(boot.stage);
  setters.setFirstPrompt(boot.firstPrompt);
  setters.setShowPrompt(boot.showPrompt);
  setters.setShowBuilder(boot.showBuilder);
  setters.setCampaign(boot.campaign);
  setters.setSessionMessages(boot.initialMessages);
  setters.setLayoutKey((k) => k + 1);
}

type BuilderLocationState = {
  isNew?: boolean;
  firstPrompt?: string;
};

export function WorkflowBuilderPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const locationState = location.state as BuilderLocationState | null;
  const pendingFirstPrompt = locationState?.firstPrompt ?? null;
  const pendingPromptConsumedRef = useRef(false);
  const effectivePendingFirstPrompt =
    pendingPromptConsumedRef.current || !pendingFirstPrompt?.trim()
      ? null
      : pendingFirstPrompt;
  const startAtPrompt =
    Boolean(locationState?.isNew) && !effectivePendingFirstPrompt?.trim();
  const invalidateWorkflowQueries = useInvalidateWorkflowQueries();

  const { data: chatThread, isFetched: chatThreadFetched } = useChatThread(workflowId);
  const { data: session } = useWorkflowSession(
    workflowId,
    chatThreadFetched && !chatThread,
  );

  const boot = useMemo(() => {
    if (!workflowId || workflowId === "new" || !chatThreadFetched) {
      return null;
    }
    return buildBuilderBoot(
      workflowId,
      { startAtPrompt, pendingFirstPrompt: effectivePendingFirstPrompt },
      session ?? null,
      chatThread ?? null,
    );
  }, [
    workflowId,
    startAtPrompt,
    effectivePendingFirstPrompt,
    session,
    chatThread,
    chatThreadFetched,
  ]);

  const [stage, setStage] = useState<BuilderStage>(() => boot?.stage ?? "builder");
  const [firstPrompt, setFirstPrompt] = useState<string | null>(
    () => boot?.firstPrompt ?? null,
  );
  const [showPrompt, setShowPrompt] = useState(() => boot?.showPrompt ?? false);
  const [showBuilder, setShowBuilder] = useState(() => boot?.showBuilder ?? true);
  const [campaign, setCampaign] = useState<CampaignMetadata>(
    () => boot?.campaign ?? { firstPrompt: null, builderStage: "builder" },
  );
  const [sessionMessages, setSessionMessages] = useState<ChatMessage[] | undefined>(
    () => boot?.initialMessages,
  );
  const [layoutKey, setLayoutKey] = useState(() => boot?.layoutKey ?? 0);

  useEffect(() => {
    if (!workflowId || workflowId === "new") {
      return;
    }
    invalidateWorkflowQueries(workflowId);
  }, [workflowId, invalidateWorkflowQueries]);

  useEffect(() => {
    if (!boot) {
      return;
    }
    applyBoot(boot, {
      setStage,
      setFirstPrompt,
      setShowPrompt,
      setShowBuilder,
      setCampaign,
      setSessionMessages,
      setLayoutKey,
    });
  }, [boot]);

  useEffect(() => {
    if (
      !workflowId ||
      !pendingFirstPrompt?.trim() ||
      pendingPromptConsumedRef.current ||
      !boot
    ) {
      return;
    }

    if (boot.firstPrompt === pendingFirstPrompt.trim()) {
      pendingPromptConsumedRef.current = true;
      navigate(campaignBuilderPath(workflowId), { replace: true, state: null });
    }
  }, [boot, pendingFirstPrompt, workflowId, navigate]);

  const promptInitialMessages = useMemo(
    () => (firstPrompt ? buildInitialChatMessages(firstPrompt) : undefined),
    [firstPrompt],
  );

  const builderInitialMessages = sessionMessages ?? promptInitialMessages;

  const handleFirstPromptSubmit = useCallback((prompt: string) => {
    setFirstPrompt(prompt);
    setSessionMessages(buildInitialChatMessages(prompt));
    setCampaign({ firstPrompt: prompt, builderStage: "builder" });
    setShowPrompt(false);

    window.setTimeout(() => {
      setStage("builder");
      setShowBuilder(true);
    }, TRANSITION_MS);
  }, []);

  const handleCampaignChange = useCallback((next: CampaignMetadata) => {
    setCampaign(next);
    if (next.builderStage === "prompt") {
      setStage("prompt");
      setShowPrompt(true);
      setShowBuilder(false);
      setFirstPrompt(null);
      setSessionMessages(undefined);
    }
  }, []);

  const handleDraftCleared = useCallback(() => {
    setSessionMessages(undefined);
    setLayoutKey((k) => k + 1);
  }, []);

  if (!workflowId || workflowId === "new") {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 3 }}>
        Workflow not found.
      </Typography>
    );
  }

  if (!chatThreadFetched) {
    return <BuilderPageSkeleton />;
  }

  if (!boot) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 3 }}>
        Workflow not found.
      </Typography>
    );
  }

  return (
    <Box
      sx={{
        position: "relative",
        overflow: "hidden",
        mx: { lg: -2 },
        my: { lg: -2 },
        width: { lg: "calc(100% + 32px)" },
        height: mainContentHeight,
        minHeight: mainContentHeight,
      }}
    >
      <Fade in={showPrompt} timeout={TRANSITION_MS} unmountOnExit>
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            zIndex: stage === "prompt" ? 1 : 0,
            pointerEvents: stage === "prompt" ? "auto" : "none",
          }}
        >
          <AiPromptScreen onSubmit={handleFirstPromptSubmit} />
        </Box>
      </Fade>

      <Fade in={showBuilder} timeout={TRANSITION_MS} unmountOnExit>
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            zIndex: stage === "builder" ? 1 : 0,
            pointerEvents: stage === "builder" ? "auto" : "none",
          }}
        >
          <BuilderLayout
            key={`${workflowId}-${layoutKey}`}
            workflowId={workflowId}
            initialMessages={builderInitialMessages}
            initialWorkflowDefinition={boot.initialWorkflowDefinition ?? null}
            initialCampaignBrief={boot.initialCampaignBrief ?? null}
            initialBriefStatus={boot.initialBriefStatus ?? null}
            initialReviewStatus={boot.initialReviewStatus ?? null}
            initialActivationAllowed={boot.initialActivationAllowed}
            campaign={campaign}
            onCampaignChange={handleCampaignChange}
            onDraftCleared={handleDraftCleared}
            layoutKey={layoutKey}
            startAtPromptOnClear={startAtPrompt}
          />
        </Box>
      </Fade>
    </Box>
  );
}
