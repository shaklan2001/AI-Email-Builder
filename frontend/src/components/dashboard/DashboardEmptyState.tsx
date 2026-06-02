import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { CreateWorkflowButton } from "./CreateWorkflowButton";

export function DashboardEmptyState() {
  return (
    <Paper
      variant="outlined"
      sx={{
        py: { xs: 6, sm: 8 },
        px: 3,
        textAlign: "center",
      }}
    >
      <Stack spacing={3} alignItems="center" maxWidth={420} mx="auto">
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 64,
            height: 64,
            borderRadius: "50%",
            bgcolor: "action.hover",
            color: "primary.main",
          }}
        >
          <AccountTreeOutlinedIcon sx={{ fontSize: 32 }} />
        </Box>

        <Stack spacing={1}>
          <Typography variant="h6">No campaigns yet</Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first campaign and let the AI sales agent build outreach for you.
          </Typography>
        </Stack>

        <CreateWorkflowButton size="large" />
      </Stack>
    </Paper>
  );
}
