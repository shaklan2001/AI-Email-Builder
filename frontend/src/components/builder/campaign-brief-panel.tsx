import CheckIcon from "@mui/icons-material/Check";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { CampaignBrief } from "../../types/campaign-brief";
import { DEFAULT_TOOLS_AVAILABLE } from "../../types/campaign-brief";

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

function resolveTools(brief: CampaignBrief): string[] {
  const tools = brief.toolsAvailable;
  if (tools && tools.length > 0) {
    return tools;
  }
  return [...DEFAULT_TOOLS_AVAILABLE];
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
  const tools = resolveTools(brief);

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
          <BriefField label="Product" value={displayValue(brief.productInfo)} />
          <BriefField label="Audience" value={displayValue(brief.audience)} />
          <BriefField label="CTA" value={displayValue(brief.cta)} />
          <BriefField label="Tone" value={displayValue(brief.tone)} />
          <BriefField label="Landing Page" value={displayValue(brief.landingPage)} />
          <BriefField label="Image URL" value={displayValue(brief.imageUrl)} />
          <BriefField label="Email Length" value={displayValue(brief.emailLength)} />
          <BriefField
            label="Follow-Up Email"
            value={displayValue(brief.followUpEnabled)}
          />
          <BriefField
            label="Follow-Up Delay"
            value={displayValue(brief.followUpDelay)}
          />
          <BriefField
            label="Reply Handling"
            value={displayValue(brief.replyHandling)}
          />

          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              Tools Available
            </Typography>
            <Stack spacing={0.5} sx={{ mt: 0.5 }}>
              {tools.map((tool) => (
                <Stack key={tool} direction="row" spacing={0.75} alignItems="center">
                  <CheckIcon sx={{ fontSize: 16, color: "success.main" }} />
                  <Typography variant="body2">{tool}</Typography>
                </Stack>
              ))}
            </Stack>
          </Box>
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
