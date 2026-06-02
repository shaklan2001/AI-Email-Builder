import PersonAddIcon from "@mui/icons-material/PersonAdd";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useState } from "react";
import type { Recipient, RecipientCounts, RecipientValidationResult } from "../../types/recipient";
import { CsvUploadDialog } from "./csv-upload-dialog";
import { ManualEntryDialog } from "./manual-entry-dialog";
import { RecipientSummary } from "./recipient-summary";

interface RecipientsPanelProps {
  counts: RecipientCounts;
  recipients: Recipient[];
  onAddEmails: (emails: string[]) => Promise<void>;
  saving?: boolean;
  saveError?: string | null;
  onDismissError?: () => void;
  requiresRecipients?: boolean;
}

export function RecipientsPanel({
  counts,
  recipients,
  onAddEmails,
  saving = false,
  saveError = null,
  onDismissError,
  requiresRecipients = false,
}: RecipientsPanelProps) {
  const [csvOpen, setCsvOpen] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);
  const [localInvalidAdded, setLocalInvalidAdded] = useState(0);

  const displayCounts: RecipientCounts = {
    validCount: counts.validCount,
    invalidCount: counts.invalidCount + localInvalidAdded,
  };

  const handleValidated = useCallback(
    async (result: RecipientValidationResult) => {
      if (result.invalid.length > 0) {
        setLocalInvalidAdded((n) => n + result.invalid.length);
      }

      if (result.valid.length > 0) {
        await onAddEmails(result.valid.map((r) => r.email));
      }
    },
    [onAddEmails],
  );

  const showRequiredHint = requiresRecipients && counts.validCount === 0;

  return (
    <>
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          px: 3,
          py: 2.5,
        }}
      >
        <Stack spacing={2.5}>
          {showRequiredHint && (
            <Alert severity="warning">
              Add at least one valid recipient before you activate this workflow. Upload a CSV
              or enter emails manually below — they are saved to your campaign immediately.
            </Alert>
          )}

          {saveError && (
            <Alert severity="error" onClose={onDismissError}>
              {saveError}
            </Alert>
          )}

          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            alignItems={{ xs: "stretch", sm: "center" }}
            justifyContent="space-between"
          >
            <RecipientSummary counts={displayCounts} />
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<UploadFileIcon />}
                onClick={() => setCsvOpen(true)}
                disabled={saving}
              >
                CSV Upload
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<PersonAddIcon />}
                onClick={() => setManualOpen(true)}
                disabled={saving}
              >
                Add Email
              </Button>
            </Stack>
          </Stack>

          {saving && (
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Saving recipients…
              </Typography>
            </Stack>
          )}

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Saved recipients
            </Typography>
            {recipients.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No recipients yet. Use CSV upload or add emails one at a time.
              </Typography>
            ) : (
              <List dense disablePadding sx={{ bgcolor: "background.paper", borderRadius: 1 }}>
                {recipients.map((recipient) => (
                  <ListItem key={recipient.id} divider>
                    <ListItemText primary={recipient.email} />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>

          <Typography variant="caption" color="text.secondary">
            CSV files should include an <strong>email</strong> column header, or use the first
            column as the email address.
          </Typography>
        </Stack>
      </Box>

      <CsvUploadDialog
        open={csvOpen}
        onClose={() => setCsvOpen(false)}
        onValidated={handleValidated}
      />
      <ManualEntryDialog
        open={manualOpen}
        onClose={() => setManualOpen(false)}
        onValidated={handleValidated}
      />
    </>
  );
}
