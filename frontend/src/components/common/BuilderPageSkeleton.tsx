import Box from "@mui/material/Box";
import { mainContentHeight } from "src/layouts/config-layout";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";

export function BuilderPageSkeleton() {
  return (
    <Box
      sx={{
        display: "flex",
        height: mainContentHeight,
        overflow: "hidden",
      }}
      aria-label="Loading workflow builder"
      aria-busy="true"
    >
      <Box
        sx={{
          width: { xs: "100%", md: 360 },
          borderRight: 1,
          borderColor: "divider",
          p: 2,
        }}
      >
        <Stack spacing={2}>
          <Skeleton variant="text" width="60%" height={28} />
          <Skeleton variant="rounded" height={120} />
          <Skeleton variant="rounded" height={48} />
          <Skeleton variant="rounded" height={48} />
        </Stack>
      </Box>
      <Box sx={{ flex: 1, p: 3, display: { xs: "none", md: "block" } }}>
        <Stack spacing={2}>
          <Skeleton variant="text" width="40%" height={32} />
          <Skeleton variant="rounded" height={200} />
          <Skeleton variant="rounded" height={160} />
        </Stack>
      </Box>
    </Box>
  );
}
