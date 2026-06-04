import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { CampaignBrief } from "../../types/campaign-brief";

const LOOKS_GOOD_MESSAGE = "Looks Good";
const EDIT_DETAILS_MESSAGE = "Edit Campaign Details";

function BriefField({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
        {value}
      </Typography>
    </Box>
  );
}

function displayValue(value: string | null | undefined): string {
  if (value && value.trim()) {
    return value.trim();
  }
  return "Not provided";
}

interface CampaignBriefPanelProps {
  brief: CampaignBrief;
  onApprove: () => void;
  onEdit: () => void;
  actionsDisabled?: boolean;
}

export function CampaignBriefPanel({
  brief,
  onApprove,
  onEdit,
  actionsDisabled = false,
}: CampaignBriefPanelProps) {
  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        p: 3,
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
      }}
    >
      <Typography variant="overline" color="text.secondary" sx={{ mb: 2 }}>
        Campaign Brief
      </Typography>

      <Paper variant="outlined" sx={{ p: 2.5, flex: 1 }}>
        <Stack spacing={2}>
          <BriefField label="Campaign Name" value={displayValue(brief.campaignName)} />
          <BriefField label="Business Goal" value={displayValue(brief.businessGoal)} />
          <BriefField label="Target Audience" value={displayValue(brief.audience)} />
          <BriefField
            label="Product / Service"
            value={displayValue(brief.productInfo)}
          />
          <BriefField label="Tone" value={displayValue(brief.tone)} />
          <BriefField label="CTA" value={displayValue(brief.cta)} />
          <BriefField label="Attachments" value={displayValue(brief.attachments)} />
          <BriefField label="Landing Page" value={displayValue(brief.landingPage)} />

          <Divider />

          <Typography variant="subtitle2">Workflow Strategy</Typography>
          <BriefField
            label="Follow-Up Strategy"
            value={displayValue(brief.followUpStrategy)}
          />
          <BriefField label="Reply Strategy" value={displayValue(brief.replyStrategy)} />
        </Stack>
      </Paper>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={{ mt: 2 }}>
        <Button
          variant="contained"
          onClick={onApprove}
          disabled={actionsDisabled}
          fullWidth
        >
          Looks Good
        </Button>
        <Button
          variant="outlined"
          onClick={onEdit}
          disabled={actionsDisabled}
          fullWidth
        >
          Edit Campaign Details
        </Button>
      </Stack>
    </Box>
  );
}

export { LOOKS_GOOD_MESSAGE, EDIT_DETAILS_MESSAGE };
