import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import MailOutlineIcon from "@mui/icons-material/MailOutline";
import PeopleOutlineIcon from "@mui/icons-material/PeopleOutline";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import Typography from "@mui/material/Typography";
import { useMemo, useState, type ReactNode } from "react";
import type { BriefStatus, CampaignBrief } from "../../types/campaign-brief";
import type { ReviewStatus } from "../../types/workflow-review";
import type { Recipient, RecipientCounts } from "../../types/recipient";
import type { WorkflowDefinition } from "../../types/workflow-definition";
import { RecipientsPanel } from "../recipients/recipients-panel";
import { CampaignBriefPanel } from "./campaign-brief-panel";
import { EmailReviewPanel } from "./email-review-panel";
import { WorkflowPreview } from "./workflow-preview";
import { WorkflowReviewPanel } from "./workflow-review-panel";

type PreviewTab = "workflow" | "email" | "recipients";

interface PreviewPanelProps {
  workflowId: string;
  workflowDefinition: WorkflowDefinition | null;
  campaignBrief: CampaignBrief | null;
  briefStatus: BriefStatus;
  onBriefApprove?: () => void;
  onBriefEdit?: () => void;
  briefActionsDisabled?: boolean;
  reviewStatus?: ReviewStatus;
  activationAllowed?: boolean;
  onReviewLooksGood?: () => void;
  onReviewEditCampaign?: () => void;
  onReviewRegenerate?: () => void;
  onActivate?: () => void;
  reviewActionsDisabled?: boolean;
  activateLoading?: boolean;
  workflowStatus?: string;
  onWorkflowChange?: (workflow: WorkflowDefinition) => void;
  recipientCounts?: RecipientCounts;
  recipients?: Recipient[];
  onAddRecipientEmails?: (emails: string[]) => Promise<void>;
  recipientsSaving?: boolean;
  recipientSaveError?: string | null;
  onDismissRecipientError?: () => void;
  onRequestRecipientsTab?: () => void;
}

function TabPanel({
  value,
  tab,
  children,
}: {
  value: PreviewTab;
  tab: PreviewTab;
  children: ReactNode;
}) {
  const active = value === tab;
  return (
    <Box
      role="tabpanel"
      hidden={!active}
      aria-labelledby={`preview-tab-${tab}`}
      sx={{
        display: active ? "flex" : "none",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      {active ? children : null}
    </Box>
  );
}

export function PreviewPanel({
  workflowId,
  workflowDefinition,
  campaignBrief,
  briefStatus,
  onBriefApprove,
  onBriefEdit,
  briefActionsDisabled = false,
  reviewStatus = null,
  activationAllowed = false,
  onReviewLooksGood,
  onReviewEditCampaign,
  onReviewRegenerate,
  onActivate,
  reviewActionsDisabled = false,
  activateLoading = false,
  workflowStatus = "draft",
  onWorkflowChange,
  recipientCounts = { validCount: 0, invalidCount: 0 },
  recipients = [],
  onAddRecipientEmails,
  recipientsSaving = false,
  recipientSaveError = null,
  onDismissRecipientError,
  onRequestRecipientsTab,
}: PreviewPanelProps) {
  const [activeTab, setActiveTab] = useState<PreviewTab>("workflow");

  const showBrief =
    briefStatus === "pending_approval" && campaignBrief !== null;
  const showReviewPanel =
    Boolean(workflowDefinition?.steps?.length) && !showBrief;

  const emailStepCount = useMemo(
    () =>
      workflowDefinition?.steps.filter(
        (s) => s.type === "send_email" && s.email,
      ).length ?? 0,
    [workflowDefinition?.steps],
  );

  const showEmailTab =
    Boolean(workflowDefinition) &&
    onWorkflowChange !== undefined &&
    !showBrief;

  const showRecipientsTab = showReviewPanel && Boolean(onAddRecipientEmails);
  const needsRecipients =
    reviewStatus === "approved" && recipientCounts.validCount === 0;

  if (showBrief && campaignBrief) {
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
        <CampaignBriefPanel
          brief={campaignBrief}
          onApprove={onBriefApprove ?? (() => undefined)}
          onEdit={onBriefEdit ?? (() => undefined)}
          actionsDisabled={briefActionsDisabled}
        />
      </Paper>
    );
  }

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
        bgcolor: "background.default",
      }}
    >
      <Box
        sx={{
          flexShrink: 0,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Tabs
          value={activeTab}
          onChange={(_, next: PreviewTab) => setActiveTab(next)}
          aria-label="Workflow builder preview"
          sx={{
            minHeight: 48,
            px: 1,
            "& .MuiTab-root": {
              minHeight: 48,
              textTransform: "none",
              fontWeight: 600,
              fontSize: "0.875rem",
            },
          }}
        >
          <Tab
            id="preview-tab-workflow"
            value="workflow"
            icon={<AccountTreeOutlinedIcon fontSize="small" />}
            iconPosition="start"
            label="Workflow"
          />
          <Tab
            id="preview-tab-email"
            value="email"
            icon={<MailOutlineIcon fontSize="small" />}
            iconPosition="start"
            label={
              emailStepCount > 0 ? `Emails (${emailStepCount})` : "Emails"
            }
            disabled={!showEmailTab || emailStepCount === 0}
          />
          {showRecipientsTab && (
            <Tab
              id="preview-tab-recipients"
              value="recipients"
              icon={<PeopleOutlineIcon fontSize="small" />}
              iconPosition="start"
              label={
                recipientCounts.validCount > 0
                  ? `Recipients (${recipientCounts.validCount})`
                  : "Recipients"
              }
              sx={
                needsRecipients
                  ? { color: "warning.main", "&.Mui-selected": { color: "warning.light" } }
                  : undefined
              }
            />
          )}
        </Tabs>
      </Box>

      <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <TabPanel value={activeTab} tab="workflow">
          <Box
            sx={{
              flex: 1,
              minHeight: 0,
              overflowY: "auto",
            }}
          >
            <WorkflowPreview
              workflowDefinition={workflowDefinition}
              campaignId={workflowId}
              showHeader={false}
            />
          </Box>
          {showReviewPanel &&
            onReviewLooksGood &&
            onReviewEditCampaign &&
            onReviewRegenerate && (
              <WorkflowReviewPanel
                reviewStatus={reviewStatus}
                activationAllowed={activationAllowed}
                recipientCount={recipientCounts.validCount}
                workflowStatus={workflowStatus}
                onLooksGood={onReviewLooksGood}
                onEditCampaign={onReviewEditCampaign}
                onRegenerate={onReviewRegenerate}
                onActivate={onActivate}
                onOpenRecipients={
                  showRecipientsTab
                    ? () => {
                        setActiveTab("recipients");
                        onRequestRecipientsTab?.();
                      }
                    : undefined
                }
                actionsDisabled={reviewActionsDisabled}
                activateLoading={activateLoading}
                embedded
              />
            )}
        </TabPanel>

        <TabPanel value={activeTab} tab="email">
          {showEmailTab && workflowDefinition && onWorkflowChange ? (
            <EmailReviewPanel
              workflowId={workflowId}
              workflowDefinition={workflowDefinition}
              onWorkflowChange={onWorkflowChange}
              onWorkflowOptimisticChange={onWorkflowChange}
              embedded
            />
          ) : (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                p: 4,
              }}
            >
              <Typography variant="body2" color="text.secondary" textAlign="center">
                Email drafts will appear here once the workflow includes send steps.
              </Typography>
            </Box>
          )}
        </TabPanel>

        {showRecipientsTab && onAddRecipientEmails && (
          <TabPanel value={activeTab} tab="recipients">
            <RecipientsPanel
              counts={recipientCounts}
              recipients={recipients}
              onAddEmails={onAddRecipientEmails}
              saving={recipientsSaving}
              saveError={recipientSaveError}
              onDismissError={onDismissRecipientError}
              requiresRecipients={reviewStatus === "approved"}
            />
          </TabPanel>
        )}
      </Box>
    </Paper>
  );
}
