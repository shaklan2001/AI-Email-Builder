import Paper from "@mui/material/Paper";
import type { Recipient, RecipientCounts } from "../../types/recipient";
import { RecipientsPanel } from "./recipients-panel";

interface RecipientManagementProps {
  counts: RecipientCounts;
  recipients: Recipient[];
  onAddEmails: (emails: string[]) => Promise<void>;
  saving?: boolean;
  saveError?: string | null;
  onDismissError?: () => void;
  requiresRecipients?: boolean;
  embedded?: boolean;
}

/** Compact bar variant kept for optional reuse; builder uses RecipientsPanel in tabs. */
export function RecipientManagement({
  embedded = false,
  ...panelProps
}: RecipientManagementProps) {
  if (embedded) {
    return <RecipientsPanel {...panelProps} />;
  }

  return (
    <Paper
      variant="outlined"
      square
      sx={{
        px: 2,
        py: 1.5,
        borderLeft: 0,
        borderRight: 0,
        borderBottom: 0,
      }}
    >
      <RecipientsPanel {...panelProps} />
    </Paper>
  );
}
