import Grid from "@mui/material/Grid2";
import { WorkflowCardSkeleton } from "./WorkflowCardSkeleton";

interface WorkflowGridSkeletonProps {
  count?: number;
}

export function WorkflowGridSkeleton({ count = 6 }: WorkflowGridSkeletonProps) {
  return (
    <Grid container spacing={3} aria-label="Loading campaigns" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <Grid key={`workflow-skeleton-${index}`} size={{ xs: 12, sm: 6, md: 4 }}>
          <WorkflowCardSkeleton />
        </Grid>
      ))}
    </Grid>
  );
}
