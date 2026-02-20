from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyConfig:
    reminder_minute: int = 5
    warning_minute: int = 10
    reassign_minute: int = 15
    escalate_minute: int = 30
    violation_threshold: int = 3
    w1_violation: float = 0.40
    w2_under_usage: float = 0.30
    w3_early_booking: float = 0.20
    w4_emergency: float = 0.10


def compute_priority_score(
    *,
    violation_rate: float,
    usage_last_7d: int,
    early_booking_minutes: int,
    emergency_flag: bool,
    max_usage_reference: int = 10,
    max_early_reference: int = 1440,
    cfg: PolicyConfig | None = None,
) -> float:
    config = cfg or PolicyConfig()

    bounded_violation = min(max(violation_rate, 0.0), 1.0)
    under_usage_factor = 1.0 - min(max(usage_last_7d / max_usage_reference, 0.0), 1.0)
    early_booking_factor = min(max(early_booking_minutes / max_early_reference, 0.0), 1.0)
    emergency = 1.0 if emergency_flag else 0.0

    score = (
        config.w1_violation * (1.0 - bounded_violation)
        + config.w2_under_usage * under_usage_factor
        + config.w3_early_booking * early_booking_factor
        + config.w4_emergency * emergency
    )
    return round(score, 4)
