import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import IconButton from "@mui/material/IconButton";
import { useTheme } from "@mui/material/styles";
import { bgBlur } from "src/theme/css";
import { useResponsive } from "src/hooks/use-responsive";
import { useNavLayout } from "./nav-layout-context";

export function NavToggleButton() {
  const theme = useTheme();
  const lgUp = useResponsive("up", "lg");
  const { collapsed, toggleCollapsed, navWidth } = useNavLayout();

  if (!lgUp) {
    return null;
  }

  return (
    <IconButton
      size="small"
      onClick={toggleCollapsed}
      aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      sx={{
        p: 0.5,
        top: 32,
        position: "fixed",
        left: navWidth - 14,
        zIndex: theme.zIndex.appBar + 1,
        border: `dashed 1px ${theme.palette.divider}`,
        bgcolor: "background.paper",
        transition: theme.transitions.create(["left"], {
          duration: theme.transitions.duration.shorter,
        }),
        ...bgBlur({ opacity: 0.72, color: theme.palette.background.default }),
        "&:hover": {
          bgcolor: "background.default",
        },
      }}
    >
      {collapsed ? (
        <ChevronRightIcon sx={{ fontSize: 18 }} />
      ) : (
        <ChevronLeftIcon sx={{ fontSize: 18 }} />
      )}
    </IconButton>
  );
}
