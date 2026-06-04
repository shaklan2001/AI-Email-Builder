import UploadFileIcon from "@mui/icons-material/UploadFile";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Typography from "@mui/material/Typography";
import { useCallback, useRef, useState } from "react";
import { parseRecipientCsv, validateRecipientEmails } from "../../lib/validate-recipient-email";
import type { RecipientValidationResult } from "../../types/recipient";

interface CsvUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onValidated: (result: RecipientValidationResult) => void;
}

export function CsvUploadDialog({ open, onClose, onValidated }: CsvUploadDialogProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const resetState = useCallback(() => {
    setFileName(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }, []);

  const handleClose = useCallback(() => {
    resetState();
    onClose();
  }, [onClose, resetState]);

  const handleFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      setError(null);

      if (!file) {
        setFileName(null);
        return;
      }

      setFileName(file.name);

      try {
        const content = await file.text();
        const emails = parseRecipientCsv(content);

        if (emails.length === 0) {
          setError("No recipient rows found in the CSV file.");
          return;
        }

        onValidated(validateRecipientEmails(emails));
        handleClose();
      } catch {
        setError("Unable to read the CSV file.");
      }
    },
    [handleClose, onValidated],
  );

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Upload CSV</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Upload a CSV file with an email column. Rows are validated for required email and
          format.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={handleFileChange}
          />
          <Button
            variant="outlined"
            startIcon={<UploadFileIcon />}
            onClick={() => inputRef.current?.click()}
          >
            Choose CSV File
          </Button>
          {fileName && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Selected: {fileName}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
}
