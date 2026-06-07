import CheckIcon from "@mui/icons-material/Check";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { ConversationThread } from "../../../conversation/conversation-thread";
import { useConversationThreadPreview } from "../../../../hooks/use-conversation-thread-preview";
import { DEFAULT_TOOLS_AVAILABLE } from "../../../../types/campaign-brief";
import type { ConversationThreadMessage } from "../../../../types/conversation-thread";
import type { AiReplyAgentNodeData } from "../types";

const MAX_AI_REPLY_COUNT = 2;

export function AiReplyAgentNode({ data }: NodeProps) {
  const { campaignId } = data as AiReplyAgentNodeData;
  const { data: threadPreview, isLoading } = useConversationThreadPreview(campaignId);
  const threadMessages: ConversationThreadMessage[] = threadPreview?.messages ?? [];
  const autoReplyCount = threadPreview?.autoReplyCount ?? 0;
  const humanReviewRequired = threadPreview?.humanReviewRequired ?? false;

  return (
    <>
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={false}
        style={{ opacity: 0, width: 8, height: 8 }}
      />
      <Paper
        variant="outlined"
        sx={{
          width: 320,
          px: 2.5,
          py: 1.5,
          borderColor: "secondary.main",
          borderWidth: 1,
          borderRadius: 1.5,
          bgcolor: "background.paper",
          boxShadow: "none",
        }}
      >
        <Typography variant="body2" fontWeight={600} textAlign="center" sx={{ mb: 1 }}>
          AI Reply Agent
        </Typography>
        <Stack spacing={1} alignItems="center">
          <Chip
            label="Auto Send Response"
            size="small"
            color="success"
            variant="outlined"
          />
          <Typography variant="caption" color="text.secondary" display="block">
            Auto replies sent: {autoReplyCount} / {MAX_AI_REPLY_COUNT}
          </Typography>
          {humanReviewRequired && (
            <Chip
              label="Human review required"
              size="small"
              color="warning"
              variant="outlined"
            />
          )}
          <Box sx={{ mt: 0.5, width: "100%", textAlign: "left" }}>
            <Typography
              variant="caption"
              color="text.secondary"
              display="block"
              sx={{ mb: 0.5 }}
            >
              Available Tools:
            </Typography>
            <Stack spacing={0.25}>
              {DEFAULT_TOOLS_AVAILABLE.map((tool) => (
                <Stack key={tool} direction="row" spacing={0.5} alignItems="center">
                  <CheckIcon sx={{ fontSize: 14, color: "success.main" }} aria-hidden />
                  <Typography variant="caption" component="span">
                    {tool}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Box>
          <Box sx={{ mt: 1, width: "100%" }}>
            {isLoading ? (
              <Typography variant="caption" color="text.secondary">
                Loading thread…
              </Typography>
            ) : threadMessages.length > 0 ? (
              <ConversationThread messages={threadMessages} />
            ) : (
              <Typography variant="caption" color="text.secondary">
                Reply threads appear here after prospects respond to your campaign emails.
              </Typography>
            )}
          </Box>
        </Stack>
      </Paper>
    </>
  );
}
