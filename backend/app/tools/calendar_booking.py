"""Calendar Booking Tool — returns a booking link for demo scheduling."""

from __future__ import annotations

from urllib.parse import urlencode

from app.core.config import settings
from app.tools.base import ToolExecutionOutput, ToolRunContext


class CalendarBookingTool:
    name = "calendar_booking"

    async def run(self, ctx: ToolRunContext) -> ToolExecutionOutput:
        params = urlencode(
            {
                "workflow_id": ctx.workflow_id,
                "lead": ctx.lead_email,
            },
        )
        base = settings.calendar_booking_url.rstrip("/")
        booking_url = f"{base}?{params}"

        summary = (
            "Happy to set up a demo. Pick a time that works for you next week:\n"
            f"{booking_url}"
        )

        return ToolExecutionOutput(
            tool=self.name,
            summary=summary,
            data={
                "booking_url": booking_url,
                "suggested_times": [
                    "Next week — morning or afternoon",
                    "Use the calendar link to confirm your slot",
                ],
                "lead_email": ctx.lead_email,
            },
        )


calendar_booking_tool = CalendarBookingTool()
