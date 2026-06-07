import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import InputBase from "@mui/material/InputBase";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { alpha, useTheme } from "@mui/material/styles";
import { useMemo, useState } from "react";
import { Aurora } from "../backgrounds/aurora";

interface AiPromptScreenProps {
  onSubmit: (prompt: string) => void;
}

export function AiPromptScreen({ onSubmit }: AiPromptScreenProps) {
  const theme = useTheme();
  const { primary } = theme.palette;
  const auroraColors = useMemo<[string, string, string]>(
    () => [primary.lighter, primary.light, primary.main],
    [primary.lighter, primary.light, primary.main],
  );
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
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        overflow: "hidden",
        bgcolor: "background.default",
      }}
    >
      <Aurora
        variant="light"
        colorStops={auroraColors}
        position="bottom"
        amplitude={0.65}
        blend={0.45}
        intensity={0.55}
        speed={0.5}
      />

      <Box
        sx={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background: `linear-gradient(
            to bottom,
            ${theme.palette.background.default} 0%,
            ${theme.palette.background.default} 52%,
            ${alpha(theme.palette.background.default, 0.78)} 72%,
            ${alpha(theme.palette.background.default, 0.25)} 100%
          )`,
        }}
      />

      <Box
        sx={{
          position: "relative",
          zIndex: 1,
          width: "100%",
          maxWidth: 720,
          px: 3,
          py: 6,
        }}
      >
        <Stack spacing={5} alignItems="center" textAlign="center">
          <Stack spacing={1.5} alignItems="center">
            <Typography
              variant="h3"
              component="h1"
              sx={{
                color: "text.primary",
                fontWeight: 700,
                letterSpacing: "-0.02em",
              }}
            >
              Build Your Outreach Campaign
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ maxWidth: 480 }}
            >
              Describe your product and audience — the AI agent will build emails
              and workflow for you.
            </Typography>
          </Stack>

          <Box
            sx={{
              width: "100%",
              borderRadius: 3,
              bgcolor: "background.paper",
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: theme.customShadows.card,
              overflow: "hidden",
            }}
          >
            <InputBase
              fullWidth
              multiline
              minRows={3}
              maxRows={6}
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
                px: 2.5,
                py: 2,
                color: "text.primary",
                fontSize: "1rem",
                lineHeight: 1.6,
                bgcolor: "background.paper",
                "& .MuiInputBase-input::placeholder": {
                  color: "text.disabled",
                  opacity: 1,
                },
              }}
            />

            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "flex-end",
                px: 1.5,
                pb: 1.5,
                bgcolor: "background.paper",
              }}
            >
              <IconButton
                onClick={handleSubmit}
                disabled={!canSubmit}
                aria-label="Start campaign"
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: canSubmit ? "primary.main" : alpha(theme.palette.grey[500], 0.12),
                  color: canSubmit ? "primary.contrastText" : "text.disabled",
                  transition: "background-color 0.2s ease, color 0.2s ease",
                  "&:hover": {
                    bgcolor: canSubmit ? "primary.dark" : alpha(theme.palette.grey[500], 0.12),
                  },
                  "&.Mui-disabled": {
                    bgcolor: alpha(theme.palette.grey[500], 0.12),
                    color: "text.disabled",
                  },
                }}
              >
                <ArrowUpwardIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
        </Stack>
      </Box>
    </Box>
  );
}
