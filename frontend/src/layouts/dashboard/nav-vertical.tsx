import { useEffect } from "react";
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Stack from "@mui/material/Stack";
import { useTheme } from "@mui/material/styles";
import Logo from "src/components/logo";
import { NavSectionMini, NavSectionVertical } from "src/components/nav-section";
import Scrollbar from "src/components/scrollbar";
import { useResponsive } from "src/hooks/use-responsive";
import { usePathname } from "src/routes/hooks/use-pathname";
import { NAV } from "../config-layout";
import { navData } from "./config-navigation";
import { NavAccount } from "./nav-account";
import { useNavLayout } from "./nav-layout-context";
import { NavToggleButton } from "./nav-toggle-button";

type Props = {
  openNav: boolean;
  onCloseNav: VoidFunction;
};

export default function NavVertical({ openNav, onCloseNav }: Props) {
  const theme = useTheme();
  const pathname = usePathname();
  const lgUp = useResponsive("up", "lg");
  const { collapsed, navWidth } = useNavLayout();

  useEffect(() => {
    if (openNav) {
      onCloseNav();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const sidebarWidth = lgUp ? navWidth : NAV.W_VERTICAL;

  const renderContent = (
    <Stack
      sx={{
        height: 1,
        minHeight: "100vh",
      }}
    >
      <Scrollbar
        sx={{
          flex: 1,
          "& .simplebar-content": {
            display: "flex",
            flexDirection: "column",
            minHeight: "100%",
          },
        }}
      >
        <Logo
          sx={{
            mt: 3,
            mb: 1,
            ...(collapsed && lgUp
              ? { mx: "auto" }
              : { ml: 4 }),
          }}
        />

        {collapsed && lgUp ? (
          <NavSectionMini
            data={navData}
            config={{
              currentRole: "admin",
            }}
          />
        ) : (
          <NavSectionVertical
            data={navData}
            config={{
              currentRole: "admin",
            }}
          />
        )}

        <Box sx={{ flexGrow: 1 }} />
      </Scrollbar>

      <NavAccount collapsed={collapsed && lgUp} />
    </Stack>
  );

  return (
    <Box
      component="nav"
      sx={{
        flexShrink: { lg: 0 },
        width: { lg: sidebarWidth },
        transition: theme.transitions.create(["width"], {
          duration: theme.transitions.duration.shorter,
        }),
      }}
    >
      <NavToggleButton />

      {lgUp ? (
        <Stack
          sx={{
            height: "100vh",
            position: "fixed",
            width: sidebarWidth,
            borderRight: (t) => `dashed 1px ${t.palette.divider}`,
            bgcolor: "background.default",
            transition: theme.transitions.create(["width"], {
              duration: theme.transitions.duration.shorter,
            }),
          }}
        >
          {renderContent}
        </Stack>
      ) : (
        <Drawer
          open={openNav}
          onClose={onCloseNav}
          PaperProps={{
            sx: {
              width: NAV.W_VERTICAL,
            },
          }}
        >
          {renderContent}
        </Drawer>
      )}
    </Box>
  );
}
