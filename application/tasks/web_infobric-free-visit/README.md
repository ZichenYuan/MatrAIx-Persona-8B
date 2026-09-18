# Infobric free first visit

MatrAIx **web** task for the "MatrAIx in the Wild" Infobric study — task **A** in
the study design. A Swedish construction professional, matched to one of four
audience tiers, lands on infobric.com, browses freely within a budget of about 25
actions, ends with a decision, and fills in a short questionnaire that includes
the pages they opened.

It is the counterpart of `web_infobric-page-audit`, which pins the persona to one
page. Running both on the same cohort answers a design question: does a free visit
produce a better result than a per-page audit — more decision variance, more
useful obstacles and suggestions, and a journey the site owner can act on?

## What it tells us

- **The journey**: which pages they open, where they stop, whether they reach
  pricing or a contact/demo/trial page, and why the visit ended.
- **The decision**: next step, primary basis, and what they would need before
  going further (`trust_action`).
- **The questionnaire**: clarity, trust, contact likelihood, what was missing, the
  biggest obstacle, and one suggested change.

## Design notes

- **Scenario**: `input/context.md` is shared verbatim with the page-audit task —
  all four tier situations, the persona picks its own. Keeping it identical means
  a comparison between the two tasks changes one thing (free visit vs. pinned page).
- **Step budget**: the instruction gives a soft budget of ~25 actions. The hard cap
  is browser-use's `MAX_STEPS` (default 50, set by the agent's `max_steps` kwarg),
  which the Playground does not yet expose per task. The soft budget leaves margin
  to save the file before the hard cap.
- **The journey is self-reported.** The verifier checks internal consistency
  (starts at the start URL; exit page is the last page listed; `reached_pricing` /
  `reached_contact` are re-derived from the URLs and emitted alongside the
  self-reported flags). The objective record is the agent's action log in the
  trial directory (`agent/browser_use.txt`, `agent/trajectory.json`), which lives
  outside the container; comparing self-report to it is an analysis step
  (`ablation/`), and the agreement rate is itself a quality metric.
- **Ratings after a long trajectory** are expected to be compressed — see
  `ablation/findings/trust-rating-collapse.md`. This task keeps `trust`,
  `clarity` and `contact_likelihood` for exactly that reason: it is the natural
  test of whether a 25-step trajectory flattens them more than a 4-step one. The
  behavioural categorical `trust_action` is the trust measure to lean on.
- **Facets**: `decision` (contract), `decision_process` (the task-spec's
  recommended context for browsing), `visit_feedback`, `site_improvement`,
  `task_outcome`. `reporting.json` groups everything by persona tier.

## Files

| File | Purpose |
|---|---|
| `instruction.md` | Task instruction, sent verbatim to the model |
| `input/context.md` | The four tier situations (shared with the page audit) |
| `tests/test_state.py` | Verifier: validity gate + facet emission |
| `reporting.json` | Per-tier distributions and LLM summaries for the batch report |
| `solution/solve.sh` | Oracle: a fixed two-page visit, no model |
| `persona_strategy.json` | Default cohort: the 1,000-persona Infobric pool, stratified by tier |

## Running

From the Playground: Web → "Infobric Free Visit". It resolves to `persona-browser-use`
from the task's runtime image. Expect roughly 5x the wall time of a page audit per
trial; run a 4-persona probe before a batch.
