import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDeleteWorkflow } from "../../hooks/use-workflows";
import type { WorkflowRecord } from "../../services/workflow.service";

interface WorkflowDeleteButtonProps {
  workflow: WorkflowRecord;
}

export function WorkflowDeleteButton({ workflow }: WorkflowDeleteButtonProps) {
  const navigate = useNavigate();
  const { workflowId: routeWorkflowId } = useParams<{ workflowId?: string }>();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const deleteMutation = useDeleteWorkflow();

  const handleOpen = () => {
    setError(null);
    setOpen(true);
  };

  const handleClose = () => {
    if (deleteMutation.isPending) {
      return;
    }
    setOpen(false);
    setError(null);
  };

  const handleConfirm = () => {
    deleteMutation.mutate(workflow.id, {
      onSuccess: () => {
        setOpen(false);
        if (routeWorkflowId === workflow.id) {
          navigate("/dashboard");
        }
      },
      onError: (err: Error) => {
        setError(err.message);
      },
    });
  };

  return (
    <>
      <Stack
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
      >
        <Button
          size="small"
          color="error"
          variant="outlined"
          startIcon={<DeleteOutlineIcon />}
          disabled={deleteMutation.isPending}
          onClick={handleOpen}
          sx={{ alignSelf: "flex-start" }}
        >
          Delete
        </Button>
      </Stack>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
        <DialogTitle>Delete workflow?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will permanently delete <strong>{workflow.name}</strong> and all
            related data (recipients, emails, analytics, and conversation history).
            This action cannot be undone.
          </DialogContentText>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={deleteMutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting…" : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
