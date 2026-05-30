"""Calendar Booking Tool — returns a booking link for demo scheduling."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from app.core.config import settings
from app.tools.base import ToolExecutionOutput, ToolRunContext


def _suggested_slots() -> list[str]:
    now = datetime.now(UTC)
    slots: list[str] = []
    for day_offset in (1, 2, 3):
        day = now + timedelta(days=day_offset)
        if day.weekday() >= 5:
            continue
        morning = day.replace(hour=10, minute=0, second=0, microsecond=0)
        afternoon = day.replace(hour=14, minute=0, second=0, microsecond=0)
        slots.append(morning.strftime("%a %b %d — 10:00 AM UTC"))
        slots.append(afternoon.strftime("%a %b %d — 2:00 PM UTC"))
        if len(slots) >= 4:
            break
    if not slots:
        slots = [
            "Next Mon — 10:00 AM UTC",
            "Next Mon — 2:00 PM UTC",
            "Next Tue — 10:00 AM UTC",
            "Next Tue — 2:00 PM UTC",
        ]
    return slots[:4]


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
        available_slots = _suggested_slots()
        slots_text = "\n".join(f"- {slot}" for slot in available_slots)

        summary = (
            "Happy to set up a demo. Here are available times next week:\n"
            f"{slots_text}\n\n"
            f"Book your slot here:\n{booking_url}"
        )

        return ToolExecutionOutput(
            tool=self.name,
            summary=summary,
            data={
                "booking_url": booking_url,
                "available_slots": available_slots,
                "lead_email": ctx.lead_email,
            },
        )


calendar_booking_tool = CalendarBookingTool()
