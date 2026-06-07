import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import { WorkflowFlowCanvas } from "./workflow-flow/workflow-flow-canvas";

interface WorkflowPreviewProps {
  workflowDefinition: WorkflowDefinition | null;
  campaignId?: string;
  showHeader?: boolean;
}

export function WorkflowPreview({
  workflowDefinition,
  campaignId,
  showHeader = true,
}: WorkflowPreviewProps) {
  const steps = workflowDefinition?.steps ?? [];
  const hasApiWorkflow = steps.length > 0;

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {showHeader && (
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ px: 3, pt: 3, pb: 1, flexShrink: 0 }}
        >
          Campaign Preview
        </Typography>
      )}

      <Box sx={{ flex: 1, minHeight: 0 }}>
        {hasApiWorkflow && workflowDefinition ? (
          <WorkflowFlowCanvas
            key={workflowDefinition.steps.map((step) => step.id).join("-")}
            workflowDefinition={workflowDefinition}
            campaignId={campaignId}
          />
        ) : (
          <Box
            sx={{
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              p: 4,
            }}
          >
            <Typography variant="body2" color="text.secondary" textAlign="center">
              Keep chatting on the left to finish setup. Your campaign draft will
              appear here as details are collected, then your workflow and emails
              after you approve the brief.
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}
