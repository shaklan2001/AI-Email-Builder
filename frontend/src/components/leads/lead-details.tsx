import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { replyIntentLabels } from "../../types/reply-intent";
import type { LeadDetails as LeadDetailsData } from "../../types/lead-details";

interface LeadDetailsProps {
  lead: LeadDetailsData;
}

export function LeadDetails({ lead }: LeadDetailsProps) {
  const displayName = lead.name ?? lead.email;

  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={1}
      alignItems={{ xs: "flex-start", sm: "center" }}
      justifyContent="space-between"
    >
      <Stack spacing={0.25}>
        <Typography variant="body2" fontWeight={600}>
          {displayName}
        </Typography>
        {lead.name ? (
          <Typography variant="caption" color="text.secondary">
            {lead.email}
          </Typography>
        ) : null}
      </Stack>

      {lead.intent ? (
        <Chip
          label={replyIntentLabels[lead.intent]}
          size="small"
          color="primary"
          variant="outlined"
          aria-label={`Reply intent: ${replyIntentLabels[lead.intent]}`}
        />
      ) : null}
    </Stack>
  );
}

interface LeadDetailsListProps {
  leads: LeadDetailsData[];
}

export function LeadDetailsList({ leads }: LeadDetailsListProps) {
  return (
    <Stack spacing={2} divider={<Divider flexItem />}>
      {leads.map((lead) => (
        <LeadDetails key={lead.email} lead={lead} />
      ))}
    </Stack>
  );
}
