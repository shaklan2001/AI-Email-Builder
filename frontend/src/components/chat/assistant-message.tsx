import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

interface AssistantMessageProps {
  content: string;
  isLoading?: boolean;
}

export function AssistantMessage({ content, isLoading = false }: AssistantMessageProps) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "flex-start",
        px: 2,
        py: 0.75,
      }}
    >
      <Paper
        variant="outlined"
        elevation={0}
        sx={{
          maxWidth: "85%",
          px: 2,
          py: 1.25,
          borderRadius: 2,
        }}
      >
        {isLoading ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <CircularProgress size={14} />
            <Typography variant="body2" color="text.secondary">
              Thinking…
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {content}
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
