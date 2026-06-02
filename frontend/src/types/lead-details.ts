import type { ReplyIntent } from "./reply-intent";

export interface LeadDetails {
  email: string;
  name?: string;
  intent?: ReplyIntent;
}
