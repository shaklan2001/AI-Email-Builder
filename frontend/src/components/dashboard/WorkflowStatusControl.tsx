import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import FormControl from "@mui/material/FormControl";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { queryKeys } from "../../api/queryKeys";
import {
  requeueWorkflowRuns,
  updateWorkflowStatus,
  type WorkflowRecord,
} from "../../services/workflow.service";
import type { WorkflowStatus } from "../../types/workflow";
import {
  workflowStatusColor,
  workflowStatusLabel,
} from "./workflow-status";

interface WorkflowStatusControlProps {
  workflow: WorkflowRecord;
  trailingActions?: ReactNode;
}

const DASHBOARD_STATUS_OPTIONS: Record<
  WorkflowStatus,
  WorkflowStatus[] | null
> = {
  draft: null,
  generating: null,
  awaiting_approval: null,
  active: ["active", "paused"],
  paused: ["paused", "active"],
  completed: null,
};

export function WorkflowStatusControl({
  workflow,
  trailingActions,
}: WorkflowStatusControlProps) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const options = DASHBOARD_STATUS_OPTIONS[workflow.status as WorkflowStatus] ?? null;
  const canChange = options !== null && options.length > 1;

  const statusMutation = useMutation({
    mutationFn: (status: "active" | "paused") =>
      updateWorkflowStatus(workflow.id, status),
    onSuccess: (result) => {
      setError(null);
      if (result.runsEnqueued > 0) {
        setInfo(`Queued ${result.runsEnqueued} email run(s). Check your inbox shortly.`);
      } else if (result.status === "active") {
        setInfo(null);
      } else {
        setInfo(null);
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
      void queryClient.invalidateQueries({ queryKey: queryKeys.analytics(workflow.id) });
    },
    onError: (err: Error) => {
      setInfo(null);
      setError(err.message);
    },
  });

  const requeueMutation = useMutation({
    mutationFn: () => requeueWorkflowRuns(workflow.id),
    onSuccess: (result) => {
      setError(null);
      setInfo(result.message);
      void queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
      void queryClient.invalidateQueries({ queryKey: queryKeys.analytics(workflow.id) });
    },
    onError: (err: Error) => {
      setInfo(null);
      setError(err.message);
    },
  });

  const handleStatusChange = (next: string) => {
    if (next === workflow.status || statusMutation.isPending) {
      return;
    }
    if (next === "active" || next === "paused") {
      statusMutation.mutate(next);
    }
  };

  const pending = statusMutation.isPending || requeueMutation.isPending;

  const showSendButton = workflow.status === "active";
  const showActionsRow = showSendButton || trailingActions;

  return (
    <Stack
      spacing={1.5}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
        <Typography variant="body2" color="text.secondary" sx={{ flexShrink: 0 }}>
          Status
        </Typography>
        {canChange ? (
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <Select
              value={workflow.status}
              onChange={(event) => handleStatusChange(event.target.value)}
              disabled={pending}
              aria-label={`Change status for ${workflow.name}`}
              sx={{ height: 32 }}
            >
              {options!.map((status) => (
                <MenuItem key={status} value={status}>
                  {workflowStatusLabel(status)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : (
          <Chip
            label={workflowStatusLabel(workflow.status)}
            color={workflowStatusColor(workflow.status)}
            size="small"
          />
        )}
      </Stack>

      {showActionsRow && (
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
          spacing={1}
          flexWrap="wrap"
          useFlexGap
        >
          <Box sx={{ display: "flex", flex: 1, minWidth: 0 }}>
            {showSendButton && (
              <Button
                size="small"
                variant="outlined"
                disabled={pending}
                onClick={() => requeueMutation.mutate()}
              >
                {requeueMutation.isPending ? "Sending…" : "Send pending emails"}
              </Button>
            )}
          </Box>
          {trailingActions}
        </Stack>
      )}

      {!canChange && workflow.status === "draft" && (
        <Typography variant="caption" color="text.secondary">
          Open the workflow to review and activate.
        </Typography>
      )}
      {info && (
        <Alert severity="success" sx={{ py: 0 }}>
          {info}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ py: 0 }}>
          {error}
        </Alert>
      )}
    </Stack>
  );
}
