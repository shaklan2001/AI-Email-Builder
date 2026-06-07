export type FollowUpDelayUnit = "minutes" | "hours" | "days" | "weeks";

export interface FollowUpDelay {
  value: number;
  unit: FollowUpDelayUnit;
}
