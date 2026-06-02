export type FollowUpDelayUnit = "hours" | "days" | "weeks";

export interface FollowUpDelay {
  value: number;
  unit: FollowUpDelayUnit;
}
