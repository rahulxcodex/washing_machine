from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import List

from laundry_agent.agent import LaundryOrchestratorAgent
from laundry_agent.models import BookingContext, DecisionTrace, QueueCandidate


@dataclass
class StubTools:
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


class TestLaundryOrchestratorAgent(unittest.TestCase):
    def test_t0_sends_multichannel_notification(self):
        now = datetime.now(UTC)
        tools = StubTools(
            booking=BookingContext("b1", "u1", "m1", cycle_completed_at=now),
            queue=[],
        )
        agent = LaundryOrchestratorAgent(tools=tools)

        trace = agent.process_tick("b1", now)

        self.assertEqual(3, len(tools.notifications))
        self.assertEqual("ELAPSED_0", trace.state)

    def test_t16_creates_violation_and_reassigns(self):
        now = datetime.now(UTC)
        tools = StubTools(
            booking=BookingContext(
                "b1",
                "u1",
                "m1",
                cycle_completed_at=now - timedelta(minutes=16),
                violation_count_30d=2,
            ),
            queue=[
                QueueCandidate("u2", "b2", usage_last_7d=1, violation_rate=0.1, early_booking_minutes=100),
                QueueCandidate("u3", "b3", usage_last_7d=5, violation_rate=0.5, early_booking_minutes=5),
            ],
        )
        agent = LaundryOrchestratorAgent(tools=tools)

        agent.process_tick("b1", now)

        policy_types = [e[0] for e in tools.policy_events]
        self.assertIn("violation", policy_types)
        self.assertIn("reassign", policy_types)
        self.assertIn("restriction", policy_types)

    def test_machine_cleared_closes_booking(self):
        now = datetime.now(UTC)
        tools = StubTools(
            booking=BookingContext(
                "b1",
                "u1",
                "m1",
                cycle_completed_at=now - timedelta(minutes=7),
                machine_cleared_at=now - timedelta(minutes=1),
            ),
            queue=[],
        )
        agent = LaundryOrchestratorAgent(tools=tools)

        trace = agent.process_tick("b1", now)

        self.assertEqual("CLEARED", trace.state)
        self.assertTrue(any(e[0] == "close_booking" for e in tools.policy_events))


if __name__ == "__main__":
    unittest.main()
