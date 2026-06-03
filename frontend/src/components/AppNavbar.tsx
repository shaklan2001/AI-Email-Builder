import { UserButton } from "@clerk/clerk-react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

export function AppNavbar() {
  return (
    <AppBar position="fixed" sx={{ height: 56, justifyContent: "center" }}>
      <Toolbar sx={{ minHeight: 56 }}>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Email Workflow Builder
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <UserButton />
        </Box>
      </Toolbar>
    </AppBar>
  );
}
