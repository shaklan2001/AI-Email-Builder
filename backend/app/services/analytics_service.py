from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.models.analytics import WorkflowAnalytics
from app.models.webhook_event import WebhookEventType
from app.repositories.analytics_repository import AnalyticsRepository, analytics_repository
from app.repositories.workflow_repository import WorkflowRepository, workflow_repository

WEBHOOK_METRIC_MAP: dict[WebhookEventType, str] = {
    "delivered": "delivered",
    "opened": "opened",
    "clicked": "clicked",
    "replied": "replied",
    "bounced": "bounced",
}


class AnalyticsService:
    def __init__(
        self,
        *,
        repository: AnalyticsRepository | None = None,
        workflow_repo: WorkflowRepository | None = None,
    ) -> None:
        self._repository = repository or analytics_repository
        self._workflow_repository = workflow_repo or workflow_repository

    async def increment(
        self,
        workflow_id: str,
        *,
        metric: str,
        amount: int = 1,
    ) -> WorkflowAnalytics:
        return await self._repository.increment(
            workflow_id,
            metric=metric,
            amount=amount,
        )

    async def record_webhook_event(
        self,
        workflow_id: str,
        event_type: WebhookEventType,
    ) -> WorkflowAnalytics | None:
        metric = WEBHOOK_METRIC_MAP.get(event_type)
        if metric is None:
            return None
        return await self.increment(workflow_id, metric=metric)

    async def record_sent(self, workflow_id: str, *, count: int = 1) -> WorkflowAnalytics:
        return await self.increment(workflow_id, metric="sent", amount=count)

    async def record_failed(self, workflow_id: str, *, count: int = 1) -> WorkflowAnalytics:
        return await self.increment(workflow_id, metric="failed", amount=count)

    async def get_for_user(
        self,
        *,
        user_id: str,
        workflow_id: str,
    ) -> WorkflowAnalytics:
        record = await self._workflow_repository.get_by_id(user_id, workflow_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found",
            )

        metrics = await self._repository.get_by_workflow_id(workflow_id)
        if metrics is not None:
            return metrics

        return WorkflowAnalytics(
            workflow_id=workflow_id,
            updated_at=datetime.now(UTC),
        )


analytics_service = AnalyticsService()
