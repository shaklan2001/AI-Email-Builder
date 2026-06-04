import Paper from "@mui/material/Paper";
import type { BriefStatus, CampaignBrief } from "../../types/campaign-brief";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import { CampaignBriefPanel } from "./campaign-brief-panel";
import { EmailReviewPanel } from "./email-review-panel";
import { WorkflowPreview } from "./workflow-preview";

interface PreviewPanelProps {
  workflowId: string;
  workflowDefinition: WorkflowDefinition | null;
  campaignBrief: CampaignBrief | null;
  briefStatus: BriefStatus;
  onBriefApprove?: () => void;
  onBriefEdit?: () => void;
  briefActionsDisabled?: boolean;
  onWorkflowChange?: (workflow: WorkflowDefinition) => void;
}

export function PreviewPanel({
  workflowId,
  workflowDefinition,
  campaignBrief,
  briefStatus,
  onBriefApprove,
  onBriefEdit,
  briefActionsDisabled = false,
  onWorkflowChange,
}: PreviewPanelProps) {
  const showBrief =
    briefStatus === "pending_approval" && campaignBrief !== null;

  return (
    <Paper
      variant="outlined"
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        borderRadius: 0,
        borderTop: 0,
        borderBottom: 0,
        borderRight: 0,
      }}
    >
      {showBrief && campaignBrief ? (
        <CampaignBriefPanel
          brief={campaignBrief}
          onApprove={onBriefApprove ?? (() => undefined)}
          onEdit={onBriefEdit ?? (() => undefined)}
          actionsDisabled={briefActionsDisabled}
        />
      ) : (
        <WorkflowPreview workflowDefinition={workflowDefinition} />
      )}
      {workflowDefinition && onWorkflowChange && !showBrief && (
        <EmailReviewPanel
          workflowId={workflowId}
          workflowDefinition={workflowDefinition}
          onWorkflowChange={onWorkflowChange}
          onWorkflowOptimisticChange={onWorkflowChange}
        />
      )}
    </Paper>
  );
}
