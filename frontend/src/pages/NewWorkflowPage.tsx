import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { queryKeys } from "../api/queryKeys";
import { campaignBuilderPath } from "../lib/campaign-routes";
import { createWorkflow } from "../services/workflow.service";

export function NewWorkflowPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const started = useRef(false);

  useEffect(() => {
    if (started.current) {
      return;
    }
    started.current = true;

    void (async () => {
      try {
        const workflow = await createWorkflow();
        await queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
        navigate(campaignBuilderPath(workflow.id), {
          replace: true,
          state: { isNew: true },
        });
      } catch {
        navigate("/dashboard", { replace: true });
      }
    })();
  }, [navigate, queryClient]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        minHeight: "calc(100vh - 56px)",
      }}
    >
      <CircularProgress size={32} />
      <Typography variant="body2" color="text.secondary">
        Creating campaign…
      </Typography>
    </Box>
  );
}
