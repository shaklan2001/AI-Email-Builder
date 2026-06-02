import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import FormControl from "@mui/material/FormControl";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
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

export function WorkflowStatusControl({ workflow }: WorkflowStatusControlProps) {
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

  return (
    <Stack
      spacing={0.5}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
          Status
        </Typography>
        {canChange ? (
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <Select
              value={workflow.status}
              onChange={(event) => handleStatusChange(event.target.value)}
              disabled={pending}
              aria-label={`Change status for ${workflow.name}`}
              sx={{ height: 28 }}
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
      {workflow.status === "active" && (
        <Button
          size="small"
          variant="outlined"
          disabled={pending}
          onClick={() => requeueMutation.mutate()}
          sx={{ alignSelf: "flex-start" }}
        >
          {requeueMutation.isPending ? "Sending…" : "Send pending emails"}
        </Button>
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
