from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class EventType(str, Enum):
    CYCLE_COMPLETED = "cycle_completed"
    MACHINE_CLEARED = "machine_cleared"
    TIMER_TICK = "timer_tick"


class ActionType(str, Enum):
    NOTIFY_OWNER = "notify_owner"
    REMINDER = "reminder"
    WARNING = "warning"
    VOICE_CALL_OWNER = "voice_call_owner"
    VIOLATION = "violation"
    REASSIGN = "reassign"
    ESCALATE_ADMIN = "escalate_admin"
    CLOSE_BOOKING = "close_booking"
    NO_OP = "no_op"


@dataclass
class BookingContext:
    booking_id: str
    user_id: str
    machine_id: str
    cycle_completed_at: datetime
    machine_cleared_at: Optional[datetime] = None
    violation_count_30d: int = 0
    emergency_flag: bool = False
    usage_last_7d: int = 0
    early_booking_minutes: int = 0


@dataclass
class QueueCandidate:
    user_id: str
    booking_id: Optional[str]
    usage_last_7d: int
    violation_rate: float
    early_booking_minutes: int
    emergency_flag: bool = False
    restricted: bool = False


@dataclass
class NotificationMessage:
    channel: str
    content: str


@dataclass
class AgentAction:
    action_type: ActionType
    booking_id: str
    reason_code: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class DecisionTrace:
    trace_id: str
    booking_id: str
    timestamp: datetime
    state: str
    actions: List[AgentAction]


def minutes_elapsed(start: datetime, now: datetime) -> int:
    return int((now - start) / timedelta(minutes=1))
