import Box, { type BoxProps } from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import { useResponsive } from "src/hooks/use-responsive";
import { useNavLayout } from "./nav-layout-context";

export default function Main({ children, sx, ...other }: BoxProps) {
  const theme = useTheme();
  const lgUp = useResponsive("up", "lg");
  const { navWidth } = useNavLayout();

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        ...(lgUp && {
          px: 2,
          py: 2,
          width: `calc(100% - ${navWidth}px)`,
          transition: theme.transitions.create(["width"], {
            duration: theme.transitions.duration.shorter,
          }),
        }),
        ...sx,
      }}
      {...other}
    >
      {children}
    </Box>
  );
}
