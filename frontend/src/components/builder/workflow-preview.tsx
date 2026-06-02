import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import CheckIcon from "@mui/icons-material/Check";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { ConversationThread } from "../conversation/conversation-thread";
import { useConversationThreadPreview } from "../../hooks/use-conversation-thread-preview";
import { getFinalEmailContent } from "../../lib/email-content";
import { waitLabelForStep } from "../../lib/format-wait-label";
import { DEFAULT_TOOLS_AVAILABLE } from "../../types/campaign-brief";
import type {
  GeneratedEmail,
  WorkflowDefinition,
  WorkflowStep,
} from "../../types/workflow-definition";
import type { ConversationThreadMessage } from "../../types/conversation-thread";

const MAX_AI_REPLY_COUNT = 2;

function truncatePreview(text: string, maxLength = 120): string {
  const singleLine = text.replace(/\s+/g, " ").trim();
  if (singleLine.length <= maxLength) {
    return singleLine;
  }
  return `${singleLine.slice(0, maxLength).trim()}…`;
}

function EmailStepDetails({ email }: { email: GeneratedEmail }) {
  const finalContent = getFinalEmailContent(email);
  return (
    <Box sx={{ mt: 1, textAlign: "left", width: "100%" }}>
      <Typography variant="caption" color="text.secondary" display="block">
        Subject
      </Typography>
      <Typography variant="body2" fontWeight={600} sx={{ mb: 0.75 }}>
        {finalContent.subject}
      </Typography>
      <Typography variant="caption" color="text.secondary" display="block">
        Preview
      </Typography>
      <Typography variant="caption" color="text.secondary" component="p" sx={{ m: 0 }}>
        {truncatePreview(finalContent.plainTextContent)}
      </Typography>
    </Box>
  );
}

function FlowStep({
  label,
  variant = "default",
  email,
}: {
  label: string;
  variant?: "default" | "branch";
  email?: GeneratedEmail;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        px: 2.5,
        py: 1.5,
        borderColor: variant === "branch" ? "secondary.main" : "primary.main",
        borderWidth: 1,
        minWidth: 200,
        maxWidth: 320,
        textAlign: "center",
      }}
    >
      <Typography variant="body2" fontWeight={500}>
        {label}
      </Typography>
      {email && <EmailStepDetails email={email} />}
    </Paper>
  );
}

function FlowArrow() {
  return (
    <ArrowDownwardIcon
      sx={{ color: "text.secondary", fontSize: 20, my: 0.5 }}
      aria-hidden
    />
  );
}

function isReplyReceivedCondition(step: WorkflowStep | undefined): boolean {
  return (
    step?.type === "reply_condition" ||
    (step?.type === "condition" && step.condition === "reply_received")
  );
}

function formatConditionLabel(condition: string): string {
  if (condition === "reply_received") {
    return "Reply?";
  }
  const words = condition.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1) + "?";
}

function AiReplyAgentStep({
  campaignId,
}: {
  campaignId?: string;
}) {
  const { data: threadPreview, isLoading } = useConversationThreadPreview(campaignId);
  const threadMessages: ConversationThreadMessage[] = threadPreview?.messages ?? [];
  const autoReplyCount = threadPreview?.autoReplyCount ?? 0;
  const humanReviewRequired = threadPreview?.humanReviewRequired ?? false;

  return (
    <Paper
      variant="outlined"
      sx={{
        px: 2.5,
        py: 1.5,
        borderColor: "secondary.main",
        borderWidth: 1,
        minWidth: 200,
        maxWidth: 320,
        textAlign: "center",
      }}
    >
      <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
        AI Reply Agent
      </Typography>
      <Stack spacing={1} alignItems="center">
        <Chip
          label="Auto Send Response"
          size="small"
          color="success"
          variant="outlined"
        />
        <Typography variant="caption" color="text.secondary" display="block">
          Auto replies sent: {autoReplyCount} / {MAX_AI_REPLY_COUNT}
        </Typography>
        {humanReviewRequired && (
          <Chip
            label="Human review required"
            size="small"
            color="warning"
            variant="outlined"
          />
        )}
        <Box sx={{ mt: 0.5, width: "100%", textAlign: "left" }}>
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
            Available Tools:
          </Typography>
          <Stack spacing={0.25}>
            {DEFAULT_TOOLS_AVAILABLE.map((tool) => (
              <Stack key={tool} direction="row" spacing={0.5} alignItems="center">
                <CheckIcon sx={{ fontSize: 14, color: "success.main" }} aria-hidden />
                <Typography variant="caption" component="span">
                  {tool}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Box>
        <Box sx={{ mt: 1.5, width: "100%" }}>
          {isLoading ? (
            <Typography variant="caption" color="text.secondary">
              Loading thread…
            </Typography>
          ) : threadMessages.length > 0 ? (
            <ConversationThread messages={threadMessages} />
          ) : (
            <Typography variant="caption" color="text.secondary">
              Reply threads appear here after prospects respond to your campaign emails.
            </Typography>
          )}
        </Box>
      </Stack>
    </Paper>
  );
}

function getStepLabel(step: WorkflowStep, followUpDelay?: WorkflowDefinition["followUpDelay"]) {
  if (step.type === "send_email") {
    return step.name ?? "Send Email";
  }
  if (step.type === "wait") {
    return waitLabelForStep(step, followUpDelay);
  }
  if (step.type === "reply_condition") {
    return "Reply?";
  }
  if (step.type === "interested_branch") {
    return step.name ?? "AI Reply Agent";
  }
  if (step.type === "no_reply_branch") {
    return "No Reply";
  }
  if (step.type === "condition" && step.condition) {
    return formatConditionLabel(step.condition);
  }
  if (step.type === "end") {
    return "End";
  }
  return step.name ?? step.type;
}

function flowStepProps(
  step: WorkflowStep,
  followUpDelay?: WorkflowDefinition["followUpDelay"],
) {
  return {
    label: getStepLabel(step, followUpDelay),
    email: step.type === "send_email" ? step.email : undefined,
  };
}

function LinearWorkflowPreview({
  steps,
  followUpDelay,
}: {
  steps: WorkflowStep[];
  followUpDelay?: WorkflowDefinition["followUpDelay"];
}) {
  return (
    <>
      {steps.map((step, index) => (
        <Box key={step.id} sx={{ display: "contents" }}>
          {index > 0 && <FlowArrow />}
          <FlowStep {...flowStepProps(step, followUpDelay)} />
        </Box>
      ))}
    </>
  );
}

function findConditionIndex(steps: WorkflowStep[]): number {
  return steps.findIndex(
    (s) =>
      s.type === "reply_condition" ||
      (s.type === "condition" && s.condition === "reply_received"),
  );
}

function ConditionalWorkflowPreview({
  steps,
  followUpDelay,
  campaignId,
}: {
  steps: WorkflowStep[];
  followUpDelay?: WorkflowDefinition["followUpDelay"];
  campaignId?: string;
}) {
  const conditionIndex = findConditionIndex(steps);
  const beforeCondition =
    conditionIndex >= 0 ? steps.slice(0, conditionIndex) : steps;
  const conditionStep =
    conditionIndex >= 0 ? steps[conditionIndex] : undefined;
  const afterCondition =
    conditionIndex >= 0 ? steps.slice(conditionIndex + 1) : [];

  const usesGenerationBranches = afterCondition.some(
    (s) => s.type === "interested_branch" || s.type === "no_reply_branch",
  );

  const yesSteps = usesGenerationBranches
    ? afterCondition.filter((s) => s.type === "interested_branch")
    : afterCondition.filter((s) => s.branch === "yes");
  const noSteps = usesGenerationBranches
    ? afterCondition.filter((s) => s.type === "send_email")
    : afterCondition.filter((s) => s.branch === "no");
  const unbranched = usesGenerationBranches
    ? []
    : afterCondition.filter((s) => !s.branch);

  const replyBranch = isReplyReceivedCondition(conditionStep);

  const yesBranchSteps =
    yesSteps.length > 0
      ? yesSteps
      : unbranched.length > 0
        ? [unbranched[0]]
        : [];
  const noBranchSteps =
    noSteps.length > 0
      ? noSteps
      : unbranched.length > 1
        ? [unbranched[1]]
        : unbranched.length === 1
          ? []
          : unbranched;

  return (
    <>
      {beforeCondition.map((step, index) => (
        <Box key={step.id} sx={{ display: "contents" }}>
          {index > 0 && <FlowArrow />}
          <FlowStep {...flowStepProps(step, followUpDelay)} />
        </Box>
      ))}

      {conditionStep && (
        <>
          {beforeCondition.length > 0 && <FlowArrow />}
          <FlowStep {...flowStepProps(conditionStep, followUpDelay)} />
        </>
      )}

      {(replyBranch || yesBranchSteps.length > 0 || noBranchSteps.length > 0) && (
        <Box
          sx={{
            display: "flex",
            gap: 3,
            mt: 2,
            width: "100%",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          {(replyBranch || yesBranchSteps.length > 0) && (
            <Stack spacing={0.5} alignItems="center" sx={{ flex: 1, minWidth: 140 }}>
              <Typography variant="caption" color="success.main" fontWeight={600}>
                Yes
              </Typography>
              {replyBranch ? (
                <>
                  <FlowArrow />
                  <AiReplyAgentStep campaignId={campaignId} />
                </>
              ) : (
                yesBranchSteps.map((step) => (
                  <Box key={step.id} sx={{ display: "contents" }}>
                    <FlowArrow />
                    <FlowStep {...flowStepProps(step, followUpDelay)} variant="branch" />
                  </Box>
                ))
              )}
            </Stack>
          )}

          {noBranchSteps.length > 0 && (
            <Stack spacing={0.5} alignItems="center" sx={{ flex: 1, minWidth: 140 }}>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                No
              </Typography>
              {noBranchSteps.map((step) => (
                <Box key={step.id} sx={{ display: "contents" }}>
                  <FlowArrow />
                  <FlowStep {...flowStepProps(step, followUpDelay)} variant="branch" />
                </Box>
              ))}
            </Stack>
          )}
        </Box>
      )}
    </>
  );
}

interface WorkflowPreviewProps {
  workflowDefinition: WorkflowDefinition | null;
  campaignId?: string;
  showHeader?: boolean;
}

export function WorkflowPreview({
  workflowDefinition,
  campaignId,
  showHeader = true,
}: WorkflowPreviewProps) {
  const steps = workflowDefinition?.steps ?? [];
  const followUpDelay = workflowDefinition?.followUpDelay;
  const workflowType = workflowDefinition?.workflowType;
  const hasApiWorkflow = steps.length > 0;

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        p: 3,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
      }}
    >
      <Stack spacing={0} alignItems="center" sx={{ maxWidth: 360, width: "100%" }}>
        {showHeader && (
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ mb: 2, alignSelf: "flex-start" }}
          >
            Campaign Preview
          </Typography>
        )}

        {hasApiWorkflow ? (
          workflowType === "conditional" ||
          workflowType === "multi_level_conditional" ||
          steps.some(
            (s) =>
              s.type === "condition" ||
              s.type === "reply_condition" ||
              s.type === "interested_branch",
          ) ? (
            <ConditionalWorkflowPreview
              steps={steps}
              followUpDelay={followUpDelay}
              campaignId={campaignId}
            />
          ) : (
            <LinearWorkflowPreview steps={steps} followUpDelay={followUpDelay} />
          )
        ) : (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: "center", py: 4, px: 2 }}
          >
            Complete the campaign setup in chat. Your workflow and emails will
            appear here once all required details are collected.
          </Typography>
        )}
      </Stack>
    </Box>
  );
}
