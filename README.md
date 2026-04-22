# Conversion Engine

Submission-focused Week 10 repo for the Tenacious Conversion Engine challenge. This repo now writes processed enrichment artifacts, audits raw-source completeness, and keeps the Act I / Act II vertical slice runnable from local data.

## Owner
- Amare Mekonnen — architecture, enrichment pipeline, orchestration, evaluation wiring

## What is now in place
- Act I benchmark scaffold with `eval/run_baseline.py`, `eval/score_log.json`, and `eval/trace_log.jsonl`
- Act II email-first orchestration with SMS fallback, HubSpot stub logging, Cal.com stub booking, conversation-state persistence, and trace logging
- Enrichment pipeline that now reads from `data/raw/crunchbase/` and `data/raw/layoffs/` when available, then falls back to local fixtures where required
- Processed briefs written automatically to `data/processed/enrichment/<company_slug>/` and lead snapshots to `data/processed/leads/`
- Raw-source audit written to `data/raw/download_status.json` so missing inputs are explicit before submission

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/audit_data_sources.py
python scripts/refresh_enrichment.py
python -m agent.orchestrator --company Ramp --recipient test@example.com
python -m agent.orchestrator --company Ramp --recipient test@example.com --reply "Yes, let's talk next week" --book
python scripts/demo_act2.py
```

## Runtime modes
- `EMAIL_MODE=draft` keeps outbound email in draft mode
- `HUBSPOT_MODE=stub` writes CRM payloads to `data/hubspot_stub.jsonl`
- `CALCOM_MODE=stub` writes bookings to `data/calcom_stub.jsonl`
- `SMS_MODE=stub` writes SMS events to `data/sms_stub.jsonl`

## Repo layout
- `agent/` orchestration, reply handling, scoring, and outbound drafting
- `briefs/` core Pydantic models for firmographics, hiring signals, AI maturity, competitor gap, bench fit, and data inventory
- `enrichment/` raw-source parsers plus enrichment builders
- `integrations/` outbound channel, HubSpot, Cal.com, trace, and state adapters
- `eval/` Act I baseline harness and benchmark outputs
- `scripts/` submission prep helpers (`audit_data_sources.py`, `refresh_enrichment.py`)
- `data/raw/` raw source drops
- `data/processed/` generated enrichment briefs and lead snapshots

## Raw data expectations
Expected source folders for Act II enrichment:
- `data/raw/crunchbase/` — Crunchbase ODM sample or normalized derivative
- `data/raw/layoffs/` — layoffs.fyi CSV
- `data/raw/job_posts/` — public job-post snapshots by `<company_slug>.json`
- `data/raw/press/` — leadership / press snapshots by `<company_slug>.json`
- `data/raw/tech_stack/` — public stack snapshots by `<company_slug>.json`

Run `python scripts/audit_data_sources.py` at any point to see what is still missing or empty.

## Interim submission readiness notes
What is ready:
- Structured lead build and trace logging
- Processed enrichment artifact generation
- HubSpot / Cal.com / SMS stubbed end-to-end flow
- Raw-source completeness audit

What still requires live credentials or fresh downloads for a fully evidence-backed interim:
- Real job-post snapshots in `data/raw/job_posts/`
- Real leadership / press snapshots in `data/raw/press/`
- Real tech-stack snapshots in `data/raw/tech_stack/`
- External `tau2-bench` checkout plus valid model credentials for rerunning Act I from scratch
- Screenshots / PDF packaging for the final handoff bundle
