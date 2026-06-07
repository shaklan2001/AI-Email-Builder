import Box from "@mui/material/Box";
import { useBoolean } from "src/hooks/use-boolean";
import { NAV } from "../config-layout";
import Main from "./main";
import { MobileNavButton } from "./mobile-nav-button";
import { NavLayoutProvider } from "./nav-layout-context";
import NavVertical from "./nav-vertical";

type Props = {
  children: React.ReactNode;
};

export default function DashboardLayout({ children }: Props) {
  const nav = useBoolean();

  return (
    <NavLayoutProvider
      expandedWidth={NAV.W_VERTICAL}
      collapsedWidth={NAV.W_MINI}
    >
      <MobileNavButton onOpen={nav.onTrue} />

      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: { xs: "column", lg: "row" },
        }}
      >
        <NavVertical openNav={nav.value} onCloseNav={nav.onFalse} />
        <Main>{children}</Main>
      </Box>
    </NavLayoutProvider>
  );
}
