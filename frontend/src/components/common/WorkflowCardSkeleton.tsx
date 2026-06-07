import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";

export function WorkflowCardSkeleton() {
  return (
    <Card variant="outlined" sx={{ height: "100%" }} aria-hidden>
      <CardContent>
        <Stack spacing={2}>
          <Skeleton variant="text" width="70%" height={32} />
          <Skeleton variant="rounded" width={96} height={28} />
          <Skeleton variant="text" width="50%" />
          <Skeleton variant="text" width="80%" />
        </Stack>
      </CardContent>
    </Card>
  );
}
