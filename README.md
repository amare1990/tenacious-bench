# Conversion Engine

Prototype repo for the TRP1 Week 10 interim submission.

## Team
- Amare Mekonnen — agent architecture, enrichment, evaluation harness

## What this repo currently covers
- Act I scaffold with deterministic local `eval/run_baseline.py` that writes `eval/score_log.json`, `eval/trace_log.jsonl`, and `baseline.md`
- Act II vertical slice for Tenacious email-first outreach with SMS fallback, HubSpot stub logging, Cal.com stub booking, and local conversation state persistence
- Local structured data for Crunchbase-style firmographics, hiring signals, AI maturity inputs, competitor-gap signals, and bench summary

## Architecture
See `docs/ARCHITECTURE.md` and `docs/interim_report.md`.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python eval/run_baseline.py
python -m agent.orchestrator --company Ramp --recipient test@example.com
python -m agent.orchestrator --company Ramp --recipient test@example.com --reply "Yes, let's talk next week" --book
python scripts/demo_act2.py
```

## Important modes
- `EMAIL_MODE=draft` keeps outbound in draft mode.
- `HUBSPOT_MODE=stub` writes CRM payloads to `data/hubspot_stub.jsonl`.
- `CALCOM_MODE=stub` writes bookings to `data/calcom_stub.jsonl`.
- `SMS_MODE=stub` writes SMS events to `data/sms_stub.jsonl`.

## Repository layout
- `agent/` orchestration, reply handling, policy logic, email and SMS agent helpers
- `enrichment/` local data-backed enrichment and scoring modules
- `integrations/` outbound channel, HubSpot, Cal.com, state, and trace adapters
- `eval/` Act I baseline harness and outputs
- `data/` local fixtures and stub outputs
- `docs/` architecture and interim-report notes

## Current gaps before a true interim-ready submission
- Replace deterministic Act I scaffold with real pinned `tau2-bench` execution
- Add real Resend/MailerSend webhook handling and real Africa's Talking callback handler
- Attach actual HubSpot MCP and Cal.com live credentials
- Produce screenshots and report PDF from live/stubbed runs
- Add a proper kill-switch flag and sink routing to satisfy deployment safeguards
