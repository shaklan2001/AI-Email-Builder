import Box from "@mui/material/Box";
import { Outlet } from "react-router-dom";
import DashboardLayout from "src/layouts/dashboard/layout";
import { ApiAuthSetup } from "./ApiAuthSetup";

export function AppLayout() {
  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <ApiAuthSetup />
      <DashboardLayout>
        <Outlet />
      </DashboardLayout>
    </Box>
  );
}
