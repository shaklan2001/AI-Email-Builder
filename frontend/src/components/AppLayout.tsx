import Box from "@mui/material/Box";
import { Outlet } from "react-router-dom";
import { ApiAuthSetup } from "./ApiAuthSetup";
import { AppNavbar } from "./AppNavbar";

export function AppLayout() {
  return (
    <Box sx={{ minHeight: "100vh" }}>
      <ApiAuthSetup />
      <AppNavbar />
      <Box component="main" sx={{ pt: "56px" }}>
        <Outlet />
      </Box>
    </Box>
  );
}
