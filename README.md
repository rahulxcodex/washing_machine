# Smart Laundry AI Agent (Reference Implementation)

This repository now includes a runnable Python AI agent implementation for the IIM Sirmaur smart laundry workflow.

## What is implemented
- `LaundryOrchestratorAgent` with T+0 / T+5 / T+10 / T+15 / T+30 state transitions.
- Multi-channel owner notifications (push/WhatsApp/SMS).
- Voice-call trigger at T+10.
- Violation + queue reassignment flow at T+15.
- Escalation at T+30.
- Priority ranking function aligned to the design doc's fairness scoring idea.
- Tool interface abstraction for plugging in real services (Twilio, WhatsApp API, DB calls).

## Files
- `laundry_agent/models.py` — domain models and action/event types
- `laundry_agent/policy.py` — policy config + priority score function
- `laundry_agent/agent.py` — orchestrator agent logic and tool contract
- `laundry_agent/demo.py` — in-memory demo runner
- `tests/test_agent.py` — unit tests for key transitions

## Run
```bash
python -m unittest -v
python -m laundry_agent.demo
```
