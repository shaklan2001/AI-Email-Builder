import PersonAddIcon from "@mui/icons-material/PersonAdd";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import { useCallback, useState } from "react";
import { addInvalidCount, addValidRecipients } from "../../mocks/recipient-storage";
import type { RecipientCounts, RecipientValidationResult } from "../../types/recipient";
import { CsvUploadDialog } from "./csv-upload-dialog";
import { ManualEntryDialog } from "./manual-entry-dialog";
import { RecipientSummary } from "./recipient-summary";

interface RecipientManagementProps {
  workflowId: string;
  counts: RecipientCounts;
  onCountsChange: () => void;
}

export function RecipientManagement({
  workflowId,
  counts,
  onCountsChange,
}: RecipientManagementProps) {
  const [csvOpen, setCsvOpen] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);

  const handleValidated = useCallback(
    (result: RecipientValidationResult) => {
      if (result.valid.length > 0) {
        addValidRecipients(workflowId, result.valid);
      }

      if (result.invalid.length > 0) {
        addInvalidCount(workflowId, result.invalid.length);
      }

      onCountsChange();
    },
    [workflowId, onCountsChange],
  );

  return (
    <>
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
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          alignItems={{ xs: "stretch", sm: "center" }}
          justifyContent="space-between"
        >
          <RecipientSummary counts={counts} />

          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<UploadFileIcon />}
              onClick={() => setCsvOpen(true)}
            >
              CSV Upload
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<PersonAddIcon />}
              onClick={() => setManualOpen(true)}
            >
              Manual Entry
            </Button>
          </Stack>
        </Stack>
      </Paper>

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
