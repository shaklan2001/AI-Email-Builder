import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import EditIcon from "@mui/icons-material/Edit";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import RefreshIcon from "@mui/icons-material/Refresh";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReviewStatus } from "../../types/workflow-review";

export const REVIEW_LOOKS_GOOD_MESSAGE = "Looks Good";
export const REVIEW_EDIT_CAMPAIGN_MESSAGE = "Edit Campaign Details";
export const REVIEW_REGENERATE_MESSAGE = "Regenerate Workflow";

interface WorkflowReviewPanelProps {
  reviewStatus: ReviewStatus;
  activationAllowed: boolean;
  recipientCount?: number;
  workflowStatus?: string;
  onLooksGood: () => void;
  onEditCampaign: () => void;
  onRegenerate: () => void;
  onActivate?: () => void;
  onOpenRecipients?: () => void;
  actionsDisabled?: boolean;
  activateLoading?: boolean;
  embedded?: boolean;
}

export function WorkflowReviewPanel({
  reviewStatus,
  activationAllowed,
  recipientCount = 0,
  onLooksGood,
  onEditCampaign,
  onRegenerate,
  onActivate,
  onOpenRecipients,
  actionsDisabled = false,
  activateLoading = false,
  workflowStatus = "draft",
  embedded = false,
}: WorkflowReviewPanelProps) {
  const approved = reviewStatus === "approved";
  const isActive = workflowStatus === "active";
  const hasRecipients = recipientCount > 0;

  return (
    <Box
      sx={{
        flexShrink: 0,
        px: 3,
        py: 2,
        borderTop: 1,
        borderColor: "divider",
        bgcolor: embedded ? "background.paper" : undefined,
      }}
    >
      {isActive ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          Workflow is active — execution has started for your recipients.
        </Alert>
      ) : approved && !hasRecipients ? (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            onOpenRecipients ? (
              <Button color="inherit" size="small" onClick={onOpenRecipients}>
                Add recipients
              </Button>
            ) : undefined
          }
        >
          Approved — add at least one recipient in the Recipients tab before activating.
        </Alert>
      ) : approved ? (
        <Alert severity="success" sx={{ mb: 2 }}>
          Approved — {recipientCount} recipient{recipientCount === 1 ? "" : "s"} ready. You can
          activate when you are ready.
        </Alert>
      ) : (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Review your workflow and emails below. Approve before activation.
        </Typography>
      )}

      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
        <Button
          variant="contained"
          startIcon={<CheckCircleOutlineIcon />}
          onClick={onLooksGood}
          disabled={actionsDisabled || approved}
          fullWidth
        >
          Looks Good
        </Button>
        <Button
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={onEditCampaign}
          disabled={actionsDisabled}
          fullWidth
        >
          Edit Campaign
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRegenerate}
          disabled={actionsDisabled}
          fullWidth
        >
          Regenerate Workflow
        </Button>
      </Stack>

      {activationAllowed && onActivate && !isActive && (
        <Button
          variant="contained"
          color="secondary"
          startIcon={<PlayArrowIcon />}
          onClick={onActivate}
          disabled={actionsDisabled || activateLoading || !hasRecipients}
          fullWidth
          sx={{ mt: 1.5 }}
        >
          {activateLoading ? "Activating…" : "Activate Workflow"}
        </Button>
      )}

      {activationAllowed && approved && !hasRecipients && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: "block" }}>
          Upload or add recipient emails before activation.
        </Typography>
      )}

      {!activationAllowed && !approved && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1.5, display: "block" }}>
          Activation is locked until you approve the workflow.
        </Typography>
      )}
    </Box>
  );
}
