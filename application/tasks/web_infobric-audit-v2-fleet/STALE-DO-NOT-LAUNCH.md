# Stale: do not launch from the UI

This directory predates the instrument-2.5 templates and the per-page traffic-mix pools.
`persona_strategy.json` here still points at the unmixed pilot-full pool with no traffic
segments, so a run started now would produce no exit/routing data at all.

Regenerate first:  uv run python application/scripts/make_audit_v2_tasks.py
(blocked while a homepage job is running: regenerating changes Harbor's job lock)
