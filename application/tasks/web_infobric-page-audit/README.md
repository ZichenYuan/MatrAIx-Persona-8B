# Infobric page audit (multi-page)

MatrAIx **web** task for the "MatrAIx in the Wild" Infobric study. A Swedish
construction professional, matched to one of four audience tiers, reviews one page
of infobric.com and files a structured audit.

**One task, many pages.** The page is chosen per job with harbor's
`extra_instruction_paths`, so the rubric and verifier exist once:

| Page | Brief | Notes |
|---|---|---|
| Homepage | `pages/homepage.md` | baseline everyone sees |
| Pricing | `pages/pricing.md` | every pilot persona flagged price as missing |
| Tier page | `pages/tier_page.md` | persona opens the page for **its own** tier; the verifier checks it did |

Add a page = one more file in `pages/` + one more job. No verifier change.

## Running one page

```bash
export LLM_BASE_URL=http://host.docker.internal:8992 LLM_API_KEY=copilot-gateway ANTHROPIC_API_KEY=copilot-gateway

uv run python application/scripts/generate_application_job.py \
  --task application/tasks/web_infobric-page-audit \
  --dataset persona/datasets/generated-persona-dev-infobric-managers-1000 \
  --no-strategy --stratify tier --stratified-allocation perCell \
  --sample-size-per-value-group 30 --seed 42 \
  --model-name anthropic/claude-haiku-4.5 --name infobric-homepage

# then add the page brief to the generated recipe:
#   extra_instruction_paths:
#     - application/tasks/web_infobric-page-audit/pages/homepage.md
uv run matraix run -c configs/jobs/application-task-job-recipe/infobric-homepage.yaml
uv run matraix results infobric-homepage --group-by tier
```

`application/scripts/make_page_jobs.py` generates all three recipes with the
brief already wired in.

## What it measures

| Field | Why |
|---|---|
| `contact_likelihood` 1-7 | headline metric. A forced categorical `next_step` collapses to one bucket depending on instruction wording (measured: 4/4 `contact_sales` with one phrasing, 4/4 `learn_more` with another); a rating scale does not. |
| `clarity` / `relevance` / `trust` 1-7 | per-page, per-tier scorecard |
| `improvement_suggestion` | "what needs to be improved **and how**", in the persona's words — clustered by tier via `reporting.json` |
| `strongest_element` / `weakest_element` | element-level attribution |
| `missing_info` / `trust_signals_noticed` | closed enums, canonicalised in the verifier |
| `reason` | the evidence quote behind every number |

Scenarios live in `input/context.md`, one per tier, each with a deadline **and a
competing option** so the supplier is not presupposed to be the answer.
