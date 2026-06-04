import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import type { WorkflowReviewData } from "../../types/workflow-review";

interface WorkflowReviewProps {
  data: WorkflowReviewData;
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

export function WorkflowReview({ data }: WorkflowReviewProps) {
  const { workflowSummary, emailSummary, recipientCount, scheduleSummary } = data;

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

      <Box sx={{ pt: 1 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<CheckCircleOutlineIcon />}
          fullWidth
        >
          Approve Workflow
        </Button>
      </Box>
    </Stack>
  );
}
