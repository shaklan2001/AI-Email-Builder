import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";

interface AiPromptScreenProps {
  onSubmit: (prompt: string) => void;
}

export function AiPromptScreen({ onSubmit }: AiPromptScreenProps) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    const trimmed = prompt.trim();
    if (!trimmed) {
      return;
    }
    onSubmit(trimmed);
  };

  const canSubmit = prompt.trim().length > 0;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        minHeight: "calc(100vh - 56px)",
        px: 3,
        py: 6,
      }}
    >
      <Stack
        spacing={4}
        alignItems="center"
        sx={{ width: "100%", maxWidth: 640, textAlign: "center" }}
      >
        <Stack spacing={1.5} alignItems="center">
          <Typography variant="h4" component="h1" fontWeight={600}>
            Build Your Outreach Campaign
          </Typography>
          <Typography variant="body1" color="text.secondary" maxWidth={480}>
            Describe your product and audience — the AI agent will build emails and workflow for you.
          </Typography>
        </Stack>

        <Stack spacing={2} sx={{ width: "100%" }}>
          <TextField
            fullWidth
            multiline
            minRows={4}
            maxRows={8}
            placeholder="Launch a new product campaign for homeowners..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && canSubmit) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            sx={{
              "& .MuiOutlinedInput-root": {
                fontSize: "1rem",
                py: 0.5,
              },
            }}
          />

          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForwardIcon />}
            onClick={handleSubmit}
            disabled={!canSubmit}
            sx={{ alignSelf: "center", minWidth: 200, px: 4 }}
          >
            Start Campaign
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}
