import EditIcon from "@mui/icons-material/Edit";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SaveIcon from "@mui/icons-material/Save";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useEffect, useState } from "react";
import { getFinalEmailContent } from "../../lib/email-content";
import { plainTextToHtml } from "../../lib/plain-text-to-html";
import { updateWorkflowEmail } from "../../services/workflow-email.service";
import type { EmailBodyVersion, WorkflowDefinition, WorkflowStep } from "../../types/workflow-definition";
import { GmailEmailEditor } from "./gmail-email-editor";

interface EmailReviewPanelProps {
  workflowId: string;
  workflowDefinition: WorkflowDefinition;
  onWorkflowChange: (workflow: WorkflowDefinition) => void;
  embedded?: boolean;
  campaignName?: string | null;
}

function getStepTitle(step: WorkflowStep): string {
  return step.name ?? "Send Email";
}

function EmailStepEditor({
  workflowId,
  step,
  onWorkflowChange,
  campaignName,
}: {
  workflowId: string;
  step: WorkflowStep;
  onWorkflowChange: (workflow: WorkflowDefinition) => void;
  campaignName?: string | null;
}) {
  const email = step.email;
  const finalContent = email ? getFinalEmailContent(email) : null;
  const [isEditing, setIsEditing] = useState(false);
  const [subject, setSubject] = useState(finalContent?.subject ?? "");
  const [plainTextContent, setPlainTextContent] = useState(
    finalContent?.plainTextContent ?? "",
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!finalContent || isEditing) {
      return;
    }
    setSubject(finalContent.subject);
    setPlainTextContent(finalContent.plainTextContent);
  }, [step.id, finalContent?.subject, finalContent?.plainTextContent, isEditing]);

  const buildContent = useCallback(
    (nextSubject: string, nextPlainText: string): EmailBodyVersion => ({
      subject: nextSubject.trim(),
      htmlContent: plainTextToHtml(nextPlainText),
      plainTextContent: nextPlainText.trim(),
    }),
    [],
  );

  const handleSave = useCallback(async () => {
    if (!subject.trim() || !plainTextContent.trim()) {
      setError("Subject and message are required.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const content = buildContent(subject, plainTextContent);
      const workflow = await updateWorkflowEmail(workflowId, step.id, content);
      onWorkflowChange(workflow);
      setIsEditing(false);
    } catch {
      setError("Could not save changes. Try again.");
    } finally {
      setSaving(false);
    }
  }, [workflowId, step.id, subject, plainTextContent, buildContent, onWorkflowChange]);

  const handleEdit = useCallback(() => {
    setError(null);
    setIsEditing(true);
  }, []);

  if (!email || !finalContent) {
    return null;
  }

  const senderName = campaignName?.trim() || "Campaign";

  return (
    <Accordion
      defaultExpanded
      disableGutters
      elevation={0}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1.5,
        overflow: "hidden",
        bgcolor: "background.paper",
        boxShadow: "none",
        "&:before": { display: "none" },
        "&.Mui-expanded": {
          margin: 0,
          boxShadow: "none",
        },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon sx={{ fontSize: 22, color: "text.secondary" }} />}
        sx={{
          minHeight: 52,
          px: 2,
          bgcolor: "background.neutral",
          borderBottom: "1px solid",
          borderColor: "divider",
          "&.Mui-expanded": {
            minHeight: 52,
          },
          "& .MuiAccordionSummary-content": {
            my: 1.25,
          },
        }}
      >
        <Typography variant="body2" fontWeight={600} color="text.primary">
          {getStepTitle(step)}
        </Typography>
        <Box
          sx={{ ml: "auto", mr: 0.5, display: "flex", alignItems: "center" }}
          onClick={(e) => e.stopPropagation()}
        >
          {isEditing ? (
            <Button
              size="small"
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={() => void handleSave()}
              disabled={saving}
            >
              {saving ? "Saving…" : "Save"}
            </Button>
          ) : (
            <Button
              size="small"
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleEdit}
            >
              Edit
            </Button>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 2, bgcolor: "background.paper" }}>
        <Stack spacing={1.5}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          <GmailEmailEditor
            subject={subject}
            body={plainTextContent}
            senderName={senderName}
            readOnly={!isEditing}
            onSubjectChange={isEditing ? setSubject : undefined}
            onBodyChange={isEditing ? setPlainTextContent : undefined}
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
  embedded = false,
  campaignName,
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
        flex: embedded ? 1 : undefined,
        minHeight: embedded ? 0 : undefined,
        overflowY: "auto",
        bgcolor: embedded ? "background.default" : "background.paper",
        borderTop: embedded ? 0 : 1,
        borderColor: "divider",
      }}
    >
      {!embedded && (
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ display: "block", px: 3, pt: 2, pb: 1 }}
        >
          Email Review
        </Typography>
      )}
      <Stack spacing={1.5} sx={{ p: embedded ? 2 : 2, pb: embedded ? 2 : 2 }}>
        {emailSteps.map((step) => (
          <EmailStepEditor
            key={step.id}
            workflowId={workflowId}
            step={step}
            onWorkflowChange={onWorkflowChange}
            campaignName={campaignName}
          />
        ))}
      </Stack>
    </Box>
  );
}
