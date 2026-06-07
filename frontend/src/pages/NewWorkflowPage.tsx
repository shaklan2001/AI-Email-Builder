import Box from "@mui/material/Box";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { mainContentHeight } from "src/layouts/config-layout";
import { queryKeys } from "../api/queryKeys";
import { AiPromptScreen } from "../components/builder/ai-prompt-screen";
import { PageLoader } from "../components/common";
import { campaignBuilderPath } from "../lib/campaign-routes";
import { createWorkflow } from "../services/workflow.service";

export function NewWorkflowPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);

  const handleFirstPromptSubmit = useCallback(
    async (prompt: string) => {
      if (creating) {
        return;
      }

      setCreating(true);
      try {
        const workflow = await createWorkflow();
        await queryClient.invalidateQueries({ queryKey: queryKeys.workflows });
        navigate(campaignBuilderPath(workflow.id), {
          replace: true,
          state: { isNew: true, firstPrompt: prompt },
        });
      } catch {
        setCreating(false);
        navigate("/dashboard", { replace: true });
      }
    },
    [creating, navigate, queryClient],
  );

  return (
    <Box
      sx={{
        position: "relative",
        overflow: "hidden",
        mx: { lg: -2 },
        my: { lg: -2 },
        width: { lg: "calc(100% + 32px)" },
        height: mainContentHeight,
        minHeight: mainContentHeight,
      }}
    >
      {creating ? (
        <PageLoader label="Creating campaign…" />
      ) : (
        <AiPromptScreen onSubmit={(prompt) => void handleFirstPromptSubmit(prompt)} />
      )}
    </Box>
  );
}
