import MenuIcon from "@mui/icons-material/Menu";
import Fab from "@mui/material/Fab";
import { useResponsive } from "src/hooks/use-responsive";

type Props = {
  onOpen: VoidFunction;
};

export function MobileNavButton({ onOpen }: Props) {
  const lgUp = useResponsive("up", "lg");

  if (lgUp) {
    return null;
  }

  return (
    <Fab
      size="small"
      color="default"
      aria-label="Open navigation"
      onClick={onOpen}
      sx={{
        position: "fixed",
        top: 16,
        left: 16,
        zIndex: (theme) => theme.zIndex.appBar + 1,
        boxShadow: (theme) => theme.customShadows.z8,
      }}
    >
      <MenuIcon fontSize="small" />
    </Fab>
  );
}
