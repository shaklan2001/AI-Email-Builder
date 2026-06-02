import { UserButton } from "@clerk/clerk-react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";

export function AppNavbar() {
  return (
    <AppBar position="fixed" sx={{ height: 56, justifyContent: "center" }}>
      <Toolbar sx={{ minHeight: 56 }}>
        <Typography
          variant="h6"
          component={RouterLink}
          to="/dashboard"
          sx={{
            flexGrow: 1,
            color: "inherit",
            textDecoration: "none",
            cursor: "pointer",
            "&:hover": { opacity: 0.9 },
          }}
        >
          AI Sales Outreach Agent
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <UserButton />
        </Box>
      </Toolbar>
    </AppBar>
  );
}
