# AI-Powered Smart Laundry Management System
## IIM Sirmaur Hostels

## 1) Executive Summary
This design proposes an AI Agent-based laundry orchestration platform that combines slot booking, real-time machine monitoring, automated nudges, voice escalation, queue optimization, and fairness controls. It targets >1000 students with clear accountability, reduced machine blocking, and measurable operational efficiency.

**Primary outcomes:**
- Prevent machine blocking via strict notification + reassignment workflow.
- Reduce conflicts with transparent queue logic and violation history.
- Improve throughput via smart slotting, buffer windows, and predictive suggestions.
- Enable admin governance with escalation and analytics dashboards.

---

## 2) Core Product Features

### A. Smart Slot Booking
- Booking channels:
  - Web app (React)
  - Mobile app (Flutter)
  - WhatsApp bot (official API)
- Configurable constraints:
  - Slot duration default: **60 min**
  - Buffer: **10 min** (cleanup/turnover)
  - Max bookings/user/day: **2**
  - Weekly cap: configurable (e.g., 8)
- Booking validations:
  - No overlapping slots per user.
  - Enforce machine capacity limits.
  - Enforce token/credit and violation restrictions.

### B. Real-Time Cycle Monitoring
Machine completion can be detected via:
1. IoT smart plug power drop pattern
2. Vibration sensor inactivity threshold
3. Smart timer start/stop integration

**Event model:**
- `cycle_started`
- `cycle_completed`
- `door_opened` (optional if hardware supports)
- `machine_cleared`

### C. Intelligent Notifications
At `cycle_completed`:
1. T+0 min: push + WhatsApp + SMS
2. T+5 min: reminder
3. T+10 min: warning + voice-call trigger
4. T+15 min: final warning + queue reassignment eligibility

If still uncleared:
- Notify next student in queue.
- Log violation for previous user.

### D. AI Voice Call Agent
At T+10 if no confirmation/clearance:
- Twilio voice bot calls current user:
  - “Your laundry on Machine M2 is complete. Remove within 5 minutes to avoid penalty.”
- If no action:
  - Call next user: “Machine expected in 5 minutes. Press 1 to confirm start.”

### E. Queue Management AI
After T+15 min uncleared state:
- Auto-transfer slot to next eligible student.
- Mark delay violation.
- After 3 violations (rolling window configurable, e.g., 30 days):
  - Temporary booking restriction (e.g., 3 days)
  - Booking priority penalty

### F. Fair Usage Algorithm
Priority score used for waitlist/overbook pressure handling:

`Priority Score = w1*(1 - violation_rate) + w2*(under_usage_factor) + w3*(early_booking_factor) + w4*(emergency_flag)`

Suggested weights:
- `w1 = 0.40`
- `w2 = 0.30`
- `w3 = 0.20`
- `w4 = 0.10`

### G. Escalation Logic
If delay exceeds **30 min**:
- Notify hostel admin and floor representative.
- Admin actions:
  - authorize manual removal
  - force-close booking
  - suspend user for policy-defined period

### H. Admin Dashboard
- Machine utilization by hour/day/hostel block
- Peak usage windows
- Avg delay & delay distribution
- Top violators & repeat offender trends
- Queue wait time trends
- Optional token revenue and recharge patterns

---

## 3) Advanced Innovations

### 3.1 Token Economy
- Monthly base credits to each student (e.g., 20 cycles).
- Violation penalties: token deductions.
- Extra bookings require token purchase.
- Dynamic pricing option during peak hours.

### 3.2 Predictive Slot Suggestions
AI predicts low-congestion windows based on historical demand.
- Suggest off-peak alternatives at booking time.
- Provide confidence interval for expected wait.

### 3.3 Crowd Heatmap
Real-time hall-level view:
- Busy/free machines
- Active queue length
- Estimated wait times

### 3.4 QR-based Start
- Each machine has unique QR.
- Student scans QR within valid slot window.
- Backend validates booking-machine-user-time mapping before enabling start.

### 3.5 AI Behavior Learning
- Track user reliability profile (delay probability, no-show rate).
- Adaptive policy:
  - responsible users get stable priority
  - repeated delays reduce priority and increase caution prompts

---

## 4) System Architecture (Scalable for 1000+ Students)

### 4.1 High-Level Stack
- **Frontend:** React.js (web admin + student PWA), Flutter (mobile)
- **Backend API:** FastAPI (Python) with async workers
- **DB:** PostgreSQL
- **Cache/Queue:** Redis (job queues, rate limits, lock handling)
- **AI Layer:**
  - LLM Agent for smart message personalization and escalation summaries
  - Rule engine for deterministic policy enforcement
  - ML model for delay prediction + slot recommendation
- **IoT Integration:** MQTT broker + ingestion service
- **Comms:**
  - Twilio (Voice + SMS)
  - WhatsApp Business API
  - Firebase Cloud Messaging (push)
- **Observability:** Prometheus + Grafana + centralized logs (ELK/OpenSearch)

### 4.2 System Flow Diagram (Text)
```text
[Student App/WhatsApp] --> [API Gateway/FastAPI] --> [Booking Service] --> [PostgreSQL]
                                       |                    |
                                       |                    --> [Queue Optimizer]
                                       |
                                       --> [Notification Orchestrator] --> [FCM / WhatsApp / SMS / Twilio Voice]

[Machine Sensor/IoT Plug] --> [MQTT Broker] --> [Machine Monitor Service] --> [Event Bus]
                                                                  |
                                                                  --> [Status Logs + Rule Engine]

[Admin Dashboard] --> [Analytics Service] --> [Warehouse/Materialized Views]
```

### 4.3 Service Responsibilities
- **Booking Service:** slot validation, caps, token checks.
- **Machine Monitor:** consumes IoT events and determines state transitions.
- **Notification Orchestrator:** timeline reminders + multi-channel fallback.
- **Queue Optimizer:** priority scoring + reassignment decisions.
- **Policy Engine:** penalties, restrictions, escalation triggers.
- **AI Assistant Service:** natural-language message variants, admin digest summaries.

---

## 5) Database Schema (Core Tables)

## 5.1 `users`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | user identifier |
| institute_id | VARCHAR(30) | UNIQUE, NOT NULL | student ID |
| full_name | VARCHAR(120) | NOT NULL | |
| phone | VARCHAR(20) | UNIQUE, NOT NULL | SMS/voice |
| whatsapp_number | VARCHAR(20) | NULL | |
| email | VARCHAR(120) | UNIQUE | |
| hostel_block | VARCHAR(20) | INDEX | |
| monthly_tokens | INT | DEFAULT 20 | |
| weekly_usage_cap | INT | DEFAULT 8 | overrideable |
| status | VARCHAR(20) | DEFAULT 'active' | active/restricted/suspended |
| created_at | TIMESTAMP | NOT NULL | |

## 5.2 `machines`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| machine_code | VARCHAR(30) | UNIQUE, NOT NULL |
| hostel_block | VARCHAR(20) | INDEX |
| floor | INT | |
| machine_type | VARCHAR(20) | washer/dryer |
| status | VARCHAR(20) | active/maintenance/offline |
| qr_code_value | VARCHAR(255) | UNIQUE |
| created_at | TIMESTAMP | NOT NULL |

## 5.3 `bookings`
| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| user_id | UUID | FK -> users(id), INDEX | |
| machine_id | UUID | FK -> machines(id), INDEX | |
| slot_start | TIMESTAMP | INDEX | |
| slot_end | TIMESTAMP | INDEX | includes buffer policy |
| status | VARCHAR(20) | INDEX | booked/in_progress/completed/reassigned/cancelled |
| booking_channel | VARCHAR(20) | web/mobile/whatsapp |
| emergency_flag | BOOLEAN | DEFAULT false | |
| priority_score | NUMERIC(5,2) | | cached score |
| token_cost | INT | DEFAULT 1 | |
| qr_validated_at | TIMESTAMP | NULL | |
| created_at | TIMESTAMP | NOT NULL | |

## 5.4 `violations`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users(id), INDEX |
| booking_id | UUID | FK -> bookings(id), UNIQUE |
| machine_id | UUID | FK -> machines(id) |
| violation_type | VARCHAR(30) | delay/no_show/misuse |
| delay_minutes | INT | |
| penalty_tokens | INT | DEFAULT 0 |
| penalty_action | VARCHAR(50) | warning/restriction/suspension |
| created_at | TIMESTAMP | INDEX |

## 5.5 `notifications`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK -> users(id), INDEX |
| booking_id | UUID | FK -> bookings(id), INDEX |
| channel | VARCHAR(20) | push/sms/whatsapp/voice |
| template_code | VARCHAR(50) | INDEX |
| delivery_status | VARCHAR(20) | queued/sent/delivered/failed |
| sent_at | TIMESTAMP | INDEX |
| provider_message_id | VARCHAR(120) | |

## 5.6 `machine_status_logs`
| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK |
| machine_id | UUID | FK -> machines(id), INDEX |
| event_type | VARCHAR(30) | INDEX |
| event_time | TIMESTAMP | INDEX |
| payload | JSONB | raw IoT payload |
| inferred_state | VARCHAR(30) | idle/running/completed/blocked |

## 5.7 `queue_records`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| machine_id | UUID | FK -> machines(id), INDEX |
| user_id | UUID | FK -> users(id), INDEX |
| booking_id | UUID | FK -> bookings(id), NULL |
| queue_position | INT | INDEX |
| priority_score | NUMERIC(5,2) | INDEX |
| status | VARCHAR(20) | waiting/notified/accepted/skipped/expired |
| created_at | TIMESTAMP | NOT NULL |

### 5.8 Indexing Strategy Summary
- Composite index: `bookings(machine_id, slot_start, slot_end)` for overlap checks.
- Composite index: `bookings(user_id, slot_start)` for daily cap checks.
- Partial index: `bookings(status)` for active bookings only.
- Composite index: `violations(user_id, created_at DESC)` for rolling-window policy.
- Time-series index: `machine_status_logs(machine_id, event_time DESC)`.
- Queue access index: `queue_records(machine_id, status, queue_position)`.

---

## 6) Agent Workflow (Step-by-Step)

1. **Booking Creation**
   - Validate caps, tokens, overlaps, restrictions.
   - Compute priority score.
   - Confirm booking and enqueue reminders.

2. **Machine Start (QR gate)**
   - User scans QR.
   - Validate user-slot-machine-time.
   - Mark booking `in_progress`; emit `cycle_started`.

3. **Cycle Monitoring**
   - IoT service streams telemetry to MQTT.
   - Monitor infers `cycle_completed`.

4. **Completion Notification Orchestration**
   - Dispatch multi-channel alerts at T+0/5/10/15.
   - Record delivery outcomes.

5. **Voice Escalation**
   - At T+10 without clearance, initiate AI voice call.

6. **Reassignment Decision**
   - At T+15 if uncleared, issue violation and notify next queued student.
   - Auto-transfer booking rights if accepted.

7. **Admin Escalation**
   - At T+30 unresolved delay, notify admin/floor rep for intervention.

8. **Logging & Learning**
   - Persist events, violations, actions.
   - Retrain delay prediction and suggestion models periodically.

---

## 7) API Design (Representative)

### Auth & Profile
- `POST /v1/auth/login`
- `GET /v1/users/me`
- `PATCH /v1/users/me/preferences`

### Booking & Queue
- `POST /v1/bookings`
- `GET /v1/bookings/my?from=&to=`
- `POST /v1/bookings/{id}/cancel`
- `GET /v1/machines/{id}/availability?date=`
- `GET /v1/machines/{id}/queue`
- `POST /v1/machines/{id}/queue/join`

### QR & Machine Lifecycle
- `POST /v1/machines/{id}/qr/start`
- `POST /v1/machines/{id}/qr/stop` (optional)
- `POST /v1/iot/events` (authenticated device ingestion)

### Notifications & Escalation
- `POST /v1/notifications/test`
- `POST /v1/escalations/{booking_id}/resolve`

### Admin Analytics
- `GET /v1/admin/analytics/usage`
- `GET /v1/admin/analytics/violations`
- `GET /v1/admin/analytics/peak-hours`
- `GET /v1/admin/reports/monthly`

---

## 8) Sample Notification Content

### Push / WhatsApp (T+0)
“Your wash cycle on Machine {{machine_code}} is complete. Please collect clothes within 10 minutes to avoid penalty.”

### Reminder (T+5)
“Reminder: Machine {{machine_code}} is waiting for pickup. 10 minutes left before violation.”

### Warning (T+10)
“Urgent: remove clothes from {{machine_code}} in 5 minutes. Voice call support is being initiated.”

### Final (T+15)
“Final alert: slot will be reassigned now and delay violation will be logged.”

### Next Queue User
“Machine {{machine_code}} expected to free in ~5 minutes. Tap to confirm your start.”

---

## 9) Voice Bot Script (Example)

### Current user escalation call
“Hi {{name}}, this is IIM Laundry Assistant. Your cycle on {{machine_code}} is complete. Please remove your clothes within 5 minutes to avoid a penalty. Press 1 if you are on the way, press 2 to release the machine.”

### Next user availability call
“Hi {{name}}, {{machine_code}} may be available in 5 minutes. Press 1 to confirm your booking start, press 2 to skip this turn.”

---

## 10) Edge Cases & Abuse Prevention

### Edge Cases
- Sensor false positives/negatives:
  - Use dual-signal confirmation (power + vibration).
- User phone unreachable:
  - Multi-channel fallback + app inbox.
- Network outages:
  - Local buffered events with retry and idempotency keys.
- No-show after booking:
  - grace window then auto-cancel + partial penalty.
- Machine maintenance sudden outage:
  - Auto-rebook impacted users by priority.

### Abuse Prevention
- QR-bound starts prevent unauthorized machine occupation.
- Rate limit booking changes/cancellations.
- Detect suspicious patterns (token farming / bot abuse).
- Tamper alerts for IoT devices (offline too often, improbable telemetry).
- Role-based admin actions with audit trail.

---

## 11) Cost Estimation (Monthly, ballpark for 1000 students)

| Component | Approx Cost (INR/month) | Notes |
|---|---:|---|
| Cloud app + DB + Redis | 25,000–45,000 | depending HA level |
| MQTT + IoT infra | 8,000–20,000 | device count dependent |
| Messaging (WhatsApp/SMS) | 10,000–35,000 | notification volume sensitive |
| Twilio Voice calls | 5,000–20,000 | escalation frequency dependent |
| Monitoring/Logging | 5,000–12,000 | |
| **Total** | **53,000–132,000** | excludes hardware capex |

**Hardware one-time (illustrative):**
- Smart plugs/sensors + QR tags per machine + install.

---

## 12) Implementation Roadmap

### Phase 0 (2 weeks): Discovery & Policy Finalization
- Hostel rules, penalty model, admin SOPs, success KPIs.

### Phase 1 MVP (6–8 weeks)
- Booking + queue + QR start
- IoT completion detection
- T+0/5/10/15 notifications
- Basic violations and admin dashboard

### Phase 2 (4–6 weeks)
- Voice bot escalation
- Fair priority score in queue
- Token wallet and deductions
- Heatmap and wait-time estimates

### Phase 3 (6–8 weeks)
- Predictive slot recommendation model
- Behavior learning and adaptive prioritization
- Full analytics reports + policy simulation tools

### Phase 4 Scale & Optimization (ongoing)
- Multi-hostel federation
- High availability tuning
- Model calibration and A/B policy experiments

---

## 13) KPI Framework
- Average machine idle-block time after cycle completion
- Violation rate per 100 bookings
- Average queue wait time
- Slot utilization (%)
- User satisfaction (NPS/CSAT)
- Admin interventions per week

---

## 14) Final Outcome Alignment with Goals
This design directly addresses the institute’s goals:
- **Eliminates machine blocking:** timed nudges + auto-reassignment + escalation.
- **Reduces conflict:** transparent queue, policy-driven penalties, digital audit trail.
- **Improves efficiency:** predictive suggestions, heatmap, utilization analytics.
- **Encourages accountability:** token economy, repeat-violation restrictions, behavior-aware prioritization.
