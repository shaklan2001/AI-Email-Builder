import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { memo } from "react";

interface UserMessageProps {
  content: string;
}

export const UserMessage = memo(function UserMessage({ content }: UserMessageProps) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-end",
        px: 2,
        py: 0.75,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          maxWidth: "85%",
          px: 2,
          py: 1.25,
          bgcolor: "primary.main",
          color: "primary.contrastText",
          borderRadius: 2,
        }}
      >
        <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
          {content}
        </Typography>
      </Paper>
    </Box>
  );
});
