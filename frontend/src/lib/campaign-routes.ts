/** Campaign-centric route helpers (workflow_id === campaign_id in API). */

export function campaignBuilderPath(campaignId: string): string {
  return `/campaigns/${campaignId}`;
}

export function campaignReviewPath(campaignId: string): string {
  return `/campaigns/${campaignId}/review`;
}

export const NEW_CAMPAIGN_PATH = "/campaigns/new";
