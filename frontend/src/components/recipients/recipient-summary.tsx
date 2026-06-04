import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { RecipientCounts } from "../../types/recipient";

interface RecipientSummaryProps {
  counts: RecipientCounts;
}

export function RecipientSummary({ counts }: RecipientSummaryProps) {
  return (
    <Stack direction="row" spacing={2} alignItems="center">
      <Typography variant="body2" color="text.secondary">
        Recipients
      </Typography>
      <Chip
        label={`Valid: ${counts.validCount}`}
        size="small"
        color="success"
        variant="outlined"
      />
      <Chip
        label={`Invalid: ${counts.invalidCount}`}
        size="small"
        color="error"
        variant="outlined"
      />
    </Stack>
  );
}
