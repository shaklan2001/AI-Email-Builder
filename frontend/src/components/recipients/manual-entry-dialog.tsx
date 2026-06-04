import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useCallback, useState } from "react";
import { validateRecipientEmails } from "../../lib/validate-recipient-email";
import type { RecipientValidationResult } from "../../types/recipient";

interface ManualEntryDialogProps {
  open: boolean;
  onClose: () => void;
  onValidated: (result: RecipientValidationResult) => void;
}

export function ManualEntryDialog({ open, onClose, onValidated }: ManualEntryDialogProps) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  const resetState = useCallback(() => {
    setEmail("");
    setError(null);
  }, []);

  const handleClose = useCallback(() => {
    resetState();
    onClose();
  }, [onClose, resetState]);

  const handleAdd = useCallback(() => {
    const trimmed = email.trim();

    if (!trimmed) {
      setError("Email is required.");
      return;
    }

    const result = validateRecipientEmails([trimmed]);
    onValidated(result);
    handleClose();
  }, [email, handleClose, onValidated]);

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Manual Entry</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Enter a recipient email address. It will be validated for required email and format.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          autoFocus
          fullWidth
          label="Email"
          type="email"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            if (error) {
              setError(null);
            }
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              handleAdd();
            }
          }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button variant="contained" onClick={handleAdd}>
          Add Recipient
        </Button>
      </DialogActions>
    </Dialog>
  );
}
