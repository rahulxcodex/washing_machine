from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Protocol
from uuid import uuid4

from .models import (
    ActionType,
    AgentAction,
    BookingContext,
    DecisionTrace,
    QueueCandidate,
    minutes_elapsed,
)
from .policy import PolicyConfig, compute_priority_score


class AgentTools(Protocol):
    def get_booking_context(self, booking_id: str) -> BookingContext: ...

    def get_queue_candidates(self, machine_id: str) -> List[QueueCandidate]: ...

    def send_notification(self, user_id: str, channel: str, content: str) -> None: ...

    def place_voice_call(self, user_id: str, script: str) -> None: ...

    def apply_policy_action(self, action_type: str, booking_id: str, reason_code: str) -> None: ...

    def log_decision(self, trace: DecisionTrace) -> None: ...


@dataclass
class LaundryOrchestratorAgent:
    tools: AgentTools
    cfg: PolicyConfig = field(default_factory=PolicyConfig)

    def process_tick(self, booking_id: str, now: datetime) -> DecisionTrace:
        ctx = self.tools.get_booking_context(booking_id)
        elapsed = minutes_elapsed(ctx.cycle_completed_at, now)
        actions: List[AgentAction] = []

        if ctx.machine_cleared_at is not None:
            action = AgentAction(ActionType.CLOSE_BOOKING, booking_id, "MACHINE_CLEARED")
            self.tools.apply_policy_action(action.action_type.value, booking_id, action.reason_code)
            actions.append(action)
            return self._trace(ctx.booking_id, now, "CLEARED", actions)

        if elapsed == 0:
            actions.extend(self._notify_owner(booking_id, ctx.user_id, "T0_COMPLETE"))

        if elapsed >= self.cfg.reminder_minute:
            actions.extend(self._notify_owner(booking_id, ctx.user_id, "T5_REMINDER"))

        if elapsed >= self.cfg.warning_minute:
            actions.extend(self._warn_and_call(booking_id, ctx.user_id))

        if elapsed >= self.cfg.reassign_minute:
            actions.extend(self._violate_and_reassign(ctx))

        if elapsed >= self.cfg.escalate_minute:
            action = AgentAction(ActionType.ESCALATE_ADMIN, booking_id, "DELAY_OVER_30")
            self.tools.apply_policy_action(action.action_type.value, booking_id, action.reason_code)
            actions.append(action)

        if not actions:
            actions.append(AgentAction(ActionType.NO_OP, booking_id, "NO_TRANSITION"))

        trace = self._trace(ctx.booking_id, now, f"ELAPSED_{elapsed}", actions)
        self.tools.log_decision(trace)
        return trace

    def rank_queue(self, machine_id: str) -> List[QueueCandidate]:
        candidates = [c for c in self.tools.get_queue_candidates(machine_id) if not c.restricted]
        return sorted(
            candidates,
            key=lambda c: compute_priority_score(
                violation_rate=c.violation_rate,
                usage_last_7d=c.usage_last_7d,
                early_booking_minutes=c.early_booking_minutes,
                emergency_flag=c.emergency_flag,
                cfg=self.cfg,
            ),
            reverse=True,
        )

    def _notify_owner(self, booking_id: str, user_id: str, reason: str) -> List[AgentAction]:
        out: List[AgentAction] = []
        for channel in ("push", "whatsapp", "sms"):
            self.tools.send_notification(user_id, channel, f"Laundry update ({reason})")
            out.append(AgentAction(ActionType.NOTIFY_OWNER, booking_id, reason, {"channel": channel}))
        return out

    def _warn_and_call(self, booking_id: str, user_id: str) -> List[AgentAction]:
        self.tools.send_notification(user_id, "whatsapp", "Urgent: remove clothes within 5 mins")
        self.tools.place_voice_call(user_id, "OWNER_ESCALATION_T10")
        return [
            AgentAction(ActionType.WARNING, booking_id, "T10_WARNING"),
            AgentAction(ActionType.VOICE_CALL_OWNER, booking_id, "T10_CALL"),
        ]

    def _violate_and_reassign(self, ctx: BookingContext) -> List[AgentAction]:
        actions = [AgentAction(ActionType.VIOLATION, ctx.booking_id, "T15_DELAY_VIOLATION")]
        self.tools.apply_policy_action(ActionType.VIOLATION.value, ctx.booking_id, "T15_DELAY_VIOLATION")

        ranked = self.rank_queue(ctx.machine_id)
        if ranked:
            next_user = ranked[0]
            self.tools.send_notification(next_user.user_id, "push", "Machine available, confirm start")
            self.tools.apply_policy_action(ActionType.REASSIGN.value, ctx.booking_id, f"NEXT_USER_{next_user.user_id}")
            actions.append(
                AgentAction(
                    ActionType.REASSIGN,
                    ctx.booking_id,
                    "REASSIGNED_TO_NEXT",
                    {"next_user": next_user.user_id},
                )
            )

        if ctx.violation_count_30d + 1 >= self.cfg.violation_threshold:
            self.tools.apply_policy_action("restriction", ctx.booking_id, "THRESHOLD_REACHED")
            actions.append(AgentAction(ActionType.VIOLATION, ctx.booking_id, "TEMP_RESTRICTION_APPLIED"))

        return actions

    @staticmethod
    def _trace(booking_id: str, now: datetime, state: str, actions: List[AgentAction]) -> DecisionTrace:
        return DecisionTrace(
            trace_id=str(uuid4()),
            booking_id=booking_id,
            timestamp=now,
            state=state,
            actions=actions,
        )
