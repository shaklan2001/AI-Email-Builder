import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";

export function ReviewPageSkeleton() {
  return (
    <Stack spacing={4} aria-label="Loading workflow review" aria-busy="true">
      <Box>
        <Skeleton variant="text" width="40%" height={36} />
        <Skeleton variant="text" width="70%" />
      </Box>
      <Skeleton variant="rounded" height={280} />
      <Stack direction="row" spacing={2}>
        <Skeleton variant="rounded" width={120} height={40} />
        <Skeleton variant="rounded" width={120} height={40} />
      </Stack>
    </Stack>
  );
}
