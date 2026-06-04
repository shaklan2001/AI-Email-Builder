import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useRef, useState } from "react";
import { getFinalEmailContent, updateWorkflowStepEmail } from "../../lib/email-content";
import { updateWorkflowEmail } from "../../services/workflow-email.service";
import type { EmailBodyVersion, WorkflowDefinition, WorkflowStep } from "../../types/workflow-definition";

const SAVE_DEBOUNCE_MS = 500;

interface EmailReviewPanelProps {
  workflowId: string;
  workflowDefinition: WorkflowDefinition;
  onWorkflowChange: (workflow: WorkflowDefinition) => void;
  onWorkflowOptimisticChange?: (workflow: WorkflowDefinition) => void;
}

function getStepTitle(step: WorkflowStep): string {
  return step.name ?? "Send Email";
}

function EmailStepEditor({
  workflowId,
  step,
  workflowDefinition,
  onWorkflowChange,
  onWorkflowOptimisticChange,
}: {
  workflowId: string;
  step: WorkflowStep;
  workflowDefinition: WorkflowDefinition;
  onWorkflowChange: (workflow: WorkflowDefinition) => void;
  onWorkflowOptimisticChange?: (workflow: WorkflowDefinition) => void;
}) {
  const email = step.email;
  const finalContent = email ? getFinalEmailContent(email) : null;
  const [subject, setSubject] = useState(finalContent?.subject ?? "");
  const [htmlContent, setHtmlContent] = useState(finalContent?.htmlContent ?? "");
  const [plainTextContent, setPlainTextContent] = useState(
    finalContent?.plainTextContent ?? "",
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!finalContent) {
      return;
    }
    setSubject(finalContent.subject);
    setHtmlContent(finalContent.htmlContent);
    setPlainTextContent(finalContent.plainTextContent);
  }, [step.id, finalContent?.subject, finalContent?.htmlContent, finalContent?.plainTextContent]);

  const persist = useCallback(async () => {
    if (!subject.trim() || !htmlContent.trim() || !plainTextContent.trim()) {
      setError("Subject, HTML, and plain text are required.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const content: EmailBodyVersion = {
        subject: subject.trim(),
        htmlContent: htmlContent.trim(),
        plainTextContent: plainTextContent.trim(),
      };
      const workflow = await updateWorkflowEmail(workflowId, step.id, content);
      onWorkflowChange(workflow);
    } catch {
      setError("Could not save changes. Try again.");
    } finally {
      setSaving(false);
    }
  }, [workflowId, step.id, subject, htmlContent, plainTextContent, onWorkflowChange]);

  const applyOptimistic = useCallback(
    (content: EmailBodyVersion) => {
      const next = updateWorkflowStepEmail(workflowDefinition, step.id, content);
      onWorkflowOptimisticChange?.(next);
    },
    [workflowDefinition, step.id, onWorkflowOptimisticChange],
  );

  const scheduleSave = useCallback(() => {
    if (saveTimer.current) {
      clearTimeout(saveTimer.current);
    }
    saveTimer.current = setTimeout(() => {
      void persist();
    }, SAVE_DEBOUNCE_MS);
  }, [persist]);

  useEffect(() => {
    return () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current);
      }
    };
  }, []);

  if (!email || !finalContent) {
    return null;
  }

  return (
    <Accordion disableGutters elevation={0} sx={{ "&:before": { display: "none" } }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} alignItems="center" sx={{ width: "100%", pr: 1 }}>
          <Typography variant="body2" fontWeight={600} sx={{ flex: 1 }}>
            {getStepTitle(step)}
          </Typography>
          {email.userEdited && (
            <Chip label="Edited" size="small" color="primary" variant="outlined" />
          )}
          {saving && (
            <Typography variant="caption" color="text.secondary">
              Saving…
            </Typography>
          )}
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Stack spacing={2}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <TextField
            label="Subject"
            value={subject}
            onChange={(e) => {
              const value = e.target.value;
              setSubject(value);
              applyOptimistic({
                subject: value,
                htmlContent,
                plainTextContent,
              });
              scheduleSave();
            }}
            fullWidth
            size="small"
          />
          <TextField
            label="HTML"
            value={htmlContent}
            onChange={(e) => {
              const value = e.target.value;
              setHtmlContent(value);
              applyOptimistic({
                subject,
                htmlContent: value,
                plainTextContent,
              });
              scheduleSave();
            }}
            fullWidth
            multiline
            minRows={6}
            size="small"
          />
          <TextField
            label="Plain text"
            value={plainTextContent}
            onChange={(e) => {
              const value = e.target.value;
              setPlainTextContent(value);
              applyOptimistic({
                subject,
                htmlContent,
                plainTextContent: value,
              });
              scheduleSave();
            }}
            fullWidth
            multiline
            minRows={4}
            size="small"
          />
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}

export function EmailReviewPanel({
  workflowId,
  workflowDefinition,
  onWorkflowChange,
  onWorkflowOptimisticChange,
}: EmailReviewPanelProps) {
  const emailSteps = workflowDefinition.steps.filter(
    (s) => s.type === "send_email" && s.email,
  );

  if (emailSteps.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        borderTop: 1,
        borderColor: "divider",
        flexShrink: 0,
        maxHeight: "45%",
        overflowY: "auto",
        bgcolor: "background.paper",
      }}
    >
      <Typography
        variant="overline"
        color="text.secondary"
        sx={{ display: "block", px: 3, pt: 2, pb: 1 }}
      >
        Email Review
      </Typography>
      <Box sx={{ px: 2, pb: 2 }}>
        {emailSteps.map((step) => (
          <EmailStepEditor
            key={step.id}
            workflowId={workflowId}
            step={step}
            workflowDefinition={workflowDefinition}
            onWorkflowChange={onWorkflowChange}
            onWorkflowOptimisticChange={onWorkflowOptimisticChange}
          />
        ))}
      </Box>
    </Box>
  );
}
