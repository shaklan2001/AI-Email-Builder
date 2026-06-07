import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { getFinalEmailContent } from "../../../../lib/email-content";
import type { EmailNodeData } from "../types";

function truncatePreview(text: string, maxLength = 120): string {
  const singleLine = text.replace(/\s+/g, " ").trim();
  if (singleLine.length <= maxLength) {
    return singleLine;
  }
  return `${singleLine.slice(0, maxLength).trim()}…`;
}

export function EmailNode({ data }: NodeProps) {
  const { label, email, variant = "default" } = data as EmailNodeData;
  const finalContent = getFinalEmailContent(email);
  const borderColor = variant === "branch" ? "secondary.main" : "primary.main";

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
          borderColor,
          borderWidth: 1,
          borderRadius: 1.5,
          bgcolor: "background.paper",
          boxShadow: "none",
        }}
      >
        <Typography variant="body2" fontWeight={600} textAlign="center">
          {label}
        </Typography>
        <Box sx={{ mt: 1, textAlign: "left" }}>
          <Typography variant="caption" color="text.secondary" display="block">
            Subject
          </Typography>
          <Typography variant="body2" fontWeight={600} sx={{ mb: 0.75 }}>
            {finalContent.subject}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Preview
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            component="p"
            sx={{ m: 0, lineHeight: 1.5 }}
          >
            {truncatePreview(finalContent.plainTextContent)}
          </Typography>
        </Box>
      </Paper>
      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={false}
        style={{ opacity: 0, width: 8, height: 8 }}
      />
    </>
  );
}
