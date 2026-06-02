import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { LeadDetailsList } from "../leads/lead-details";
import { LEAD_STATUSES, leadStatusLabels } from "../../types/lead-status";
import type { LeadStatusCounts, WorkflowReviewData } from "../../types/workflow-review";

interface WorkflowReviewProps {
  data: WorkflowReviewData;
  onLooksGood?: () => void;
  onEditCampaign?: () => void;
  onRegenerate?: () => void;
  onActivate?: () => void;
  actionsDisabled?: boolean;
  approveLoading?: boolean;
}

function ReviewSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle1" component="h2" fontWeight={600} gutterBottom>
          {title}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

export function WorkflowReview({
  data,
  onLooksGood,
  onEditCampaign,
  onRegenerate,
  onActivate,
  actionsDisabled = false,
  approveLoading = false,
}: WorkflowReviewProps) {
  const {
    workflowSummary,
    emailSummary,
    recipientCount,
    scheduleSummary,
    leadStatusCounts,
    leadDetails = [],
  } = data;
  const statusCounts: LeadStatusCounts | null = leadStatusCounts ?? null;
  const showLeadStatus = statusCounts !== null && Object.keys(statusCounts).length > 0;
  const approved = data.reviewStatus === "approved";

  return (
    <Stack spacing={3}>
      <ReviewSection title="Workflow Summary">
        <Stack spacing={1}>
          <Typography variant="body2" color="text.secondary">
            {workflowSummary.name}
          </Typography>
          <Typography variant="body2">{workflowSummary.description}</Typography>
          <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
            {workflowSummary.steps.map((step) => (
              <Typography key={step} component="li" variant="body2">
                {step}
              </Typography>
            ))}
          </Box>
        </Stack>
      </ReviewSection>

      <ReviewSection title="Email Summary">
        <Stack spacing={1}>
          <Typography variant="body2">
            <Typography component="span" variant="body2" fontWeight={600}>
              Subject:{" "}
            </Typography>
            {emailSummary.subject}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {emailSummary.bodyPreview}
          </Typography>
        </Stack>
      </ReviewSection>

      <ReviewSection title="Recipient Count">
        <Typography variant="h4" component="p">
          {recipientCount.toLocaleString()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          valid recipients ready to receive this workflow
        </Typography>
      </ReviewSection>

      <ReviewSection title="Schedule Summary">
        <Stack spacing={0.5} divider={<Divider flexItem />}>
          <Typography variant="body2">
            <Typography component="span" fontWeight={600}>
              Start date:{" "}
            </Typography>
            {scheduleSummary.startDate}
          </Typography>
          <Typography variant="body2">
            <Typography component="span" fontWeight={600}>
              Timezone:{" "}
            </Typography>
            {scheduleSummary.timezone}
          </Typography>
          <Typography variant="body2">
            <Typography component="span" fontWeight={600}>
              Send window:{" "}
            </Typography>
            {scheduleSummary.sendWindow}
          </Typography>
        </Stack>
      </ReviewSection>

      {showLeadStatus && statusCounts && (
        <ReviewSection title="Lead Status">
          <Stack
            direction="row"
            flexWrap="wrap"
            gap={1}
            aria-label="Lead lifecycle status counts"
          >
            {LEAD_STATUSES.map((status) => (
              <Chip
                key={status}
                label={`${leadStatusLabels[status]}: ${(statusCounts[status] ?? 0).toLocaleString()}`}
                size="small"
                variant="outlined"
              />
            ))}
          </Stack>
        </ReviewSection>
      )}

      {leadDetails.length > 0 && (
        <ReviewSection title="Lead Details">
          <LeadDetailsList leads={leadDetails} />
        </ReviewSection>
      )}

      <Box sx={{ pt: 1 }}>
        <Stack spacing={1.5}>
          {approved && (
            <Typography variant="body2" color="success.main">
              Workflow approved — activation is unlocked.
            </Typography>
          )}
          <Button
            variant="contained"
            size="large"
            startIcon={<CheckCircleOutlineIcon />}
            fullWidth
            onClick={onLooksGood}
            disabled={actionsDisabled || approved || approveLoading}
          >
            {approveLoading ? "Approving…" : "Looks Good"}
          </Button>
          {onEditCampaign && (
            <Button
              variant="outlined"
              fullWidth
              onClick={onEditCampaign}
              disabled={actionsDisabled || approveLoading}
            >
              Edit Campaign
            </Button>
          )}
          {onRegenerate && (
            <Button
              variant="outlined"
              fullWidth
              onClick={onRegenerate}
              disabled={actionsDisabled || approveLoading}
            >
              Regenerate Workflow
            </Button>
          )}
          {onActivate && data.activationAllowed && (
            <Button
              variant="contained"
              color="secondary"
              fullWidth
              onClick={onActivate}
              disabled={actionsDisabled}
            >
              Activate Workflow
            </Button>
          )}
        </Stack>
      </Box>
    </Stack>
  );
}
