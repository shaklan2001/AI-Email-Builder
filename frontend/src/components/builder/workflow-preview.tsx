import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getFinalEmailContent } from "../../lib/email-content";
import type {
  GeneratedEmail,
  WorkflowDefinition,
  WorkflowStep,
} from "../../types/workflow-definition";
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

function formatConditionLabel(condition: string): string {
  const words = condition.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1) + "?";
}

function getStepLabel(step: WorkflowStep): string {
  if (step.type === "send_email") {
    return step.name ?? "Send Email";
  }
  if (step.type === "wait") {
    const days = step.days ?? 3;
    const dayWord = days === 1 ? "Day" : "Days";
    return `Wait ${days} ${dayWord}`;
  }
  if (step.type === "condition" && step.condition) {
    return formatConditionLabel(step.condition);
  }
  if (step.type === "end") {
    return "End";
  }
  return step.name ?? step.type;
}

function flowStepProps(step: WorkflowStep) {
  return {
    label: getStepLabel(step),
    email: step.type === "send_email" ? step.email : undefined,
  };
}

function LinearWorkflowPreview({ steps }: { steps: WorkflowStep[] }) {
  return (
    <>
      {steps.map((step, index) => (
        <Box key={step.id} sx={{ display: "contents" }}>
          {index > 0 && <FlowArrow />}
          <FlowStep {...flowStepProps(step)} />
        </Box>
      ))}
    </>
  );
}

function ConditionalWorkflowPreview({ steps }: { steps: WorkflowStep[] }) {
  const conditionIndex = steps.findIndex((s) => s.type === "condition");
  const beforeCondition =
    conditionIndex >= 0 ? steps.slice(0, conditionIndex) : steps;
  const conditionStep =
    conditionIndex >= 0 ? steps[conditionIndex] : undefined;
  const afterCondition =
    conditionIndex >= 0 ? steps.slice(conditionIndex + 1) : [];

  const yesSteps = afterCondition.filter((s) => s.branch === "yes");
  const noSteps = afterCondition.filter((s) => s.branch === "no");
  const unbranched = afterCondition.filter((s) => !s.branch);

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
          <FlowStep {...flowStepProps(step)} />
        </Box>
      ))}

      {conditionStep && (
        <>
          {beforeCondition.length > 0 && <FlowArrow />}
          <FlowStep {...flowStepProps(conditionStep)} />
        </>
      )}

      {(yesBranchSteps.length > 0 || noBranchSteps.length > 0) && (
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
          {yesBranchSteps.length > 0 && (
            <Stack spacing={0.5} alignItems="center" sx={{ flex: 1, minWidth: 140 }}>
              <Typography variant="caption" color="success.main" fontWeight={600}>
                Yes
              </Typography>
              {yesBranchSteps.map((step) => (
                <Box key={step.id} sx={{ display: "contents" }}>
                  <FlowArrow />
                  <FlowStep {...flowStepProps(step)} variant="branch" />
                </Box>
              ))}
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
                  <FlowStep {...flowStepProps(step)} variant="branch" />
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
}

export function WorkflowPreview({
  workflowDefinition,
}: WorkflowPreviewProps) {
  const steps = workflowDefinition?.steps ?? [];
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
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ mb: 2, alignSelf: "flex-start" }}
        >
          Workflow Preview
        </Typography>

        {hasApiWorkflow ? (
          workflowType === "conditional" ||
          workflowType === "multi_level_conditional" ||
          steps.some((s) => s.type === "condition") ? (
            <ConditionalWorkflowPreview steps={steps} />
          ) : (
            <LinearWorkflowPreview steps={steps} />
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
