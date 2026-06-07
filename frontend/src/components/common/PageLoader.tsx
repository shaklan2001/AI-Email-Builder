import Box from "@mui/material/Box";
import { mainContentHeight } from "src/layouts/config-layout";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";

interface PageLoaderProps {
  label?: string;
  minHeight?: string | number | Record<string, string | number>;
}

export function PageLoader({
  label,
  minHeight = mainContentHeight,
}: PageLoaderProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        minHeight,
        py: 6,
      }}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <CircularProgress size={32} aria-hidden />
      {label ? (
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      ) : null}
    </Box>
  );
}
