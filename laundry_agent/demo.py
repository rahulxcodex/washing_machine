from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import List

from .agent import LaundryOrchestratorAgent
from .models import BookingContext, DecisionTrace, QueueCandidate


@dataclass
class InMemoryTools:
    booking: BookingContext
    queue: List[QueueCandidate]
    policy_events: List[tuple] = field(default_factory=list)
    notifications: List[tuple] = field(default_factory=list)
    calls: List[tuple] = field(default_factory=list)
    traces: List[DecisionTrace] = field(default_factory=list)

    def get_booking_context(self, booking_id: str) -> BookingContext:
        return self.booking

    def get_queue_candidates(self, machine_id: str) -> List[QueueCandidate]:
        return self.queue

    def send_notification(self, user_id: str, channel: str, content: str) -> None:
        self.notifications.append((user_id, channel, content))

    def place_voice_call(self, user_id: str, script: str) -> None:
        self.calls.append((user_id, script))

    def apply_policy_action(self, action_type: str, booking_id: str, reason_code: str) -> None:
        self.policy_events.append((action_type, booking_id, reason_code))

    def log_decision(self, trace: DecisionTrace) -> None:
        self.traces.append(trace)


def run_demo() -> None:
    now = datetime.now(UTC)
    tools = InMemoryTools(
        booking=BookingContext(
            booking_id="b1",
            user_id="u1",
            machine_id="m1",
            cycle_completed_at=now - timedelta(minutes=16),
            violation_count_30d=2,
        ),
        queue=[
            QueueCandidate("u2", "b2", usage_last_7d=1, violation_rate=0.0, early_booking_minutes=200),
            QueueCandidate("u3", "b3", usage_last_7d=5, violation_rate=0.2, early_booking_minutes=30),
        ],
    )

    agent = LaundryOrchestratorAgent(tools=tools)
    trace = agent.process_tick("b1", now)

    print("state:", trace.state)
    print("actions:", [a.action_type.value for a in trace.actions])
    print("policy_events:", tools.policy_events)


if __name__ == "__main__":
    run_demo()
