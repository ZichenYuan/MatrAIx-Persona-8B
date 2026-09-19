# Infobric page audit v2 (master)

MatrAIx **web** task for the Infobric website pilot, built around the partner's brief
(Main Brief + five URL briefs) and their 90-day analytics. One page per generated task,
reviewed as a standalone entry point, with one click on the page's primary next-step
button. Design: `docs/superpowers/specs/2026-09-18-infobric-audit-v2-design.md`.

**This directory is the master. Do not launch it directly.** Generate the per-page tasks:

    uv run python application/scripts/make_audit_v2_tasks.py

which produces `web_infobric-audit-v2-<page>` for every page that has a brief in
`pages/`, plus a `-skim` variant when `pages/variants/skim.md` exists.

## Files

| File | Purpose |
|---|---|
| `instruction.md` | The rubric, sent verbatim to the model; `<!-- PAGE BRIEF -->` is replaced by the page brief |
| `pages/<page>.md` | Page brief: URL, purpose, primary button to inspect, `next_step` options |
| `pages/<page>.context.md` | → `input/context.md`: the page's purpose in neutral words (harbor prepends it) |
| `pages/<page>.inventory.json` | → `input/inventory.json`: hand-checked ground truth (draft with `build_inventory.py`) |
| `tests/test_state.py` | Verifier: validity gate, grounding against the inventory, facet emission |
| `reporting.json` | Per-visitor-kind distributions and LLM summaries in the partner's report shape |
| `solution/solve.sh` | Oracle: opens the page, clicks the CTA once, writes a valid artifact |
| `persona_strategy.json` | Default cohort: pilot-full pool, stratified by `audience_group`; per-page filter set by the generator |

## Persona contract

Personas come from `persona/datasets/generated-persona-dev-infobric-pilot-full`
(`persona/scripts/cohort_configs/PILOT_PERSONAS.md`). The task reads `visit_intent`
for a fidelity check and relies on the persona carrying its own situation; the task
ships no scenario text and no analytics numbers.

## Adding a page

1. `pages/<page>.md` — copy `homepage.md`, set page_id, URL, purpose (from the partner's
   URL brief), the primary button, and the `next_step` options that exist on the page.
2. `pages/<page>.context.md` — two short paragraphs, neutral.
3. `uv run python application/scripts/build_inventory.py --page-id <page> --url <url>`
   then hand-check the draft: truth statement, CTA labels and targets, exact claims,
   conversion vs navigation next steps.
4. Add the page's persona filter to `PAGES` in `make_audit_v2_tasks.py`, regenerate,
   register in `playground_task_registry.py`, restart the backend.
5. Oracle run, then a 4-6 persona probe before any batch.
