# Ablation plan: measuring the quality of a persona simulation

This branch holds the tooling for comparing simulation runs against each other —
different models, agents, persona pools, instrument wordings, pages. It builds on
the Infobric study on the `partner` branch and uses its tasks, cohort and runs as
the first data.

Everything below is grounded in runs from 2026-09-12 → 2026-09-16. Numbers cited
are measured, not assumed; where we have no measurement yet it says so.

## 1. Why the current headline number cannot be the metric

Every batch report leads with **mean reward**. Reward is the verifier's pass/fail:
did the agent produce a valid `page_audit.json` that satisfies the schema. It
measures whether the pipeline *ran*, not whether the output contains information.

Two homepage runs this week both scored ≈1.0 and differed enormously in quality:

| run | agent + model | reward | `trust` sd | `next_step` at modal value |
|---|---|---|---|---|
| `…-4044ed9a` (n=100) | playwright + claude-haiku-4.5 | 1.00 | 0.55 | 79% |
| `…-d26dac30` (n=84) | browser-use + gpt-5.6-luna | 0.90 | **0.00** | **100%** |

The second run's `trust` field was the same value for every one of 76 personas.
Reward did not notice. Ablations must therefore score **validity** and
**discrimination**, and treat reward only as a gate.

## 2. What "quality of the simulation" means

A simulation run is good to the extent that:

1. **It ran** — trials complete, artifacts parse, cost and time are bounded.
2. **The persona reached the output** — a different persona produces a
   different answer, in the direction the persona implies.
3. **The instrument separates segments** — fields that are supposed to vary by
   audience actually do, beyond noise.
4. **The agent saw the real page** — claims about the page are true of the page.
5. **The signal is stable** — re-running the same persona gives the same answer.
6. **The output is usable** — the free text is concrete and actionable.

Each dimension gets its own metrics. A config can win on one and lose on another
(browser-use wins on 4 and loses nothing; gpt-5.6-luna loses on 3), so we never
collapse them into a single score.

## 3. Metric catalogue

All metrics are computed per job from `result.json`, `aggregation.json`, the
per-trial `page_audit.json` artifacts, and the persona YAML each trial used.
"Baseline" is the homepage run `pg-web-infobric-audit-homepage-d26dac30`
(browser-use, gpt-5.6-luna, n=76 usable) unless stated.

### 3.1 Pipeline health — gate, do not rank on it

| metric | definition | baseline |
|---|---|---|
| completion rate | trials with a parseable artifact / trials requested | 76/84 = 90% |
| error rate | errored trials / trials | 7/84; the tier-page probe was 25% before the blank-page recovery line, 8% after |
| `json_health` clean rate | artifacts parsing strictly, without control characters | 1 of 77 needed lenient parse |
| wall time / trial | job duration / trials, at stated concurrency | ≈42 s at concurrency 3; 100 trials ≈ 70 min |
| cost / trial | from `stats.cost_usd` | **untracked for browser-use — reports $0.** Must be fixed before cost comparisons mean anything |

A config that fails the gate is not compared further; report why.

### 3.2 Persona fidelity — did the persona reach the output?

| metric | definition | baseline |
|---|---|---|
| **tier-recall** | share of audits whose free text (`reason`, `strongest_element`, `weakest_element`, `improvement_suggestion`, `one_sentence_summary`) matches the persona's *assigned* tier better than any other tier, by keyword | **93%** vs 25% chance |
| tier-mention | share whose free text mentions the assigned tier at all | 95% |

This is the first thing to check in any model or pool ablation. A model that
ignores the persona produces output that looks *consistent* and is worthless.
The keyword lists live in `instrument_health.py`; extend them per study.

Conditioning travels via `PERSONA_SYSTEM` into the agent's system prompt
(~22k characters per persona) and is **not** echoed to the agent log, so absence
from logs proves nothing — measure behaviourally.

### 3.3 Discrimination — does the instrument separate segments?

For every numeric self-report field, per job:

| metric | definition | baseline (homepage, luna) |
|---|---|---|
| sd | population sd across all personas | contact 0.41 · clarity 0.31 · relevance 0.26 · **trust 0.00** |
| range used | min–max actually emitted on the 1–7 scale | contact 3–4 · clarity 4–6 · relevance 5–7 · trust 5–5 |
| between-tier η² | share of variance explained by tier (one-way ANOVA) | contact **0.27** · clarity 0.14 · relevance 0.11 · trust 0.00 |
| F, p | same test; F-crit(3,72) ≈ 2.73 at p=.05 | contact 8.9 · clarity 4.0 · relevance 3.0 · trust 0 |

For every categorical field:

| metric | definition | baseline |
|---|---|---|
| modal share | share at the most common value | `next_step` 100% `learn_more`; `basis_primary` 24% `fit` |
| entropy | Shannon entropy of the distribution, bits | `next_step` 0.0 |
| per-tier modal | modal share within each tier | — |

Interpretation rules:

- **η² and rank order are comparable across arms. Means are not.** A single
  guidance line moved `contact_likelihood` from 4.38 to 2.38 with sd unchanged
  (0.48 → 0.48). Levels are instrument artifacts.
- Ordinal integers over a 2–3 point range violate ANOVA assumptions; at n≈76 the
  F-test is robust enough to rank fields, not to publish p-values.
- Statistically alive ≠ useful. `clarity` had a real tier effect (η²=0.14) over
  a 0.30-point spread — enough to order tiers, not enough to quote.

### 3.4 Observational accuracy — did the agent see the page?

These are ground-truthable against a hand-checked inventory per page (§4). They
are the metrics most sensitive to the **agent**.

| metric | definition | baseline |
|---|---|---|
| trust-signal recall | for each signal present on the page, share of audits reporting it | logos **76/76** (browser-use) vs **0/2** (playwright); testimonial 52/76; case_studies 33/76 |
| trust-signal precision | share of reported signals actually present | not yet measured |
| key-claim grounding | `key_claim_noticed` is a substring of the page text | not yet measured |
| `missing_info` false positives | items reported missing that the page contains (e.g. `price` on the pricing page, which shows 325–805 kr) | not yet measured |
| palette grounding | colours named in `tone_and_visuals` appear in the site CSS | "dark blue and orange" in 4/4 vision trials; DOM-only trials named colours they could not see |
| tier-page URL correctness | already a verifier facet (`tier_page_correct`) | 3/3 in the probe |

The logo case is the canonical example: the six customer logos (NCC, Skanska,
Peab, Veidekke, Assemblin, Renta) all carry `alt=""`, so a DOM-only agent cannot
see them. Its 0/2 is a structural false negative, not sampling noise.

### 3.5 Reliability — is it signal or noise?

| metric | definition | baseline |
|---|---|---|
| test-retest agreement | same persona ids, same page, same config, run twice; per numeric field: exact-match share and mean |Δ|; per categorical: Cohen's κ | **not measured — the largest gap in this plan** |
| cross-arm rank agreement | Spearman ρ between arms on per-tier means | not measured |

Without test-retest we cannot tell whether a field's between-persona variance is
discrimination or randomness. η² only means something relative to this floor.
One repeat of the baseline arm (84 trials, ~1 h) fixes this.

### 3.6 Usefulness — is the free text worth reading?

| metric | definition |
|---|---|
| concreteness | share of `strongest_element` / `weakest_element` naming a specific element (the rubric requires it) |
| suggestion themes per tier | number of clusters in `improvement_suggestion` within a tier |
| cross-tier overlap | share of themes shared by all tiers (low overlap = tiers want different things) |

The `reporting.json` LLM bucket summaries already produce these qualitatively;
quantifying them is lower priority than §3.2–3.5.

## 4. Ground truth needed per page

One JSON file per page under `ablation/ground_truth/`, hand-checked against the
live site and dated:

```json
{
  "page_id": "homepage",
  "url": "https://infobric.com/se/",
  "checked": "2026-09-16",
  "trust_signals_present": ["logos", "customer_count", "testimonial", "case_studies"],
  "logo_names": ["NCC", "Skanska", "Peab", "Veidekke", "Assemblin", "Renta"],
  "customer_count_claim": "Betrodd av över 12 000 kunder och 450 000 användare",
  "shows_price": false,
  "palette": ["dark blue", "orange", "white"],
  "key_claims": ["..."]
}
```

Pricing page: `shows_price: true` (325, 435, 805, 550, 385 kr visible). Tier
pages: one entry per tier URL.

## 5. Ablation design rules

Learned the hard way this week — the homepage comparison changed agent, model
*and* instrument at once, and attribution had to be reconstructed from old jobs.

1. **One factor per arm.** Everything else pinned, including the instruction
   text (hash it into the run metadata).
2. **Paired personas.** Save the cohort as a dataset (Playground → "Save as
   dataset…") and reuse the same persona ids in every arm. Then per-persona
   deltas are measurable and a repeated arm is the noise floor.
3. **Declare primaries before running.** Proposed: tier-recall,
   `contact_likelihood` η², `basis_primary` modal share, logo + key-claim recall.
   Everything else is exploratory.
4. **State the detectable effect.** ~20 per tier detects *d*≈1.3 with power
   >0.95 (the size of the contact_likelihood effect); *d*≈0.5 needs ~64 per
   tier. Say which you are powered for.
5. **Compare effect sizes and rank orders, never raw means** (§3.3).
6. **Fresh job names every run.** Harbor replays a job directory's original
   config if the name is reused.
7. **Concurrency 3.** Docker has 8.3 GB; each trial requests 2 GB; four
   concurrent is too tight for a multi-hour run.

## 6. Planned arms

### 6.1 Model (highest priority)

Evidence so far says the model, not the agent, drives numeric collapse:
`cmp2-playwright` and `cmp2-browseruse` (both gpt-5.6-luna, n=2) were equally
flat; `azure-smoke` (gpt-4.1-mini) and the haiku run varied.

| arm | model | status / caveat |
|---|---|---|
| A | gpt-5.6-luna | baseline, n=76 done |
| B | gpt-6-astra | untested |
| C | gpt-5.6-sol | accepts `reasoning.effort`; untested at scale |
| D | DeepSeek-V4-Pro | untested |
| E | claude-haiku-4.5 | requires `ANTHROPIC_BASE_URL` → `host.docker.internal:8992`; `127.0.0.1` is unreachable from containers |
| — | gpt-4.1-mini | **excluded**: intermittent `reasoning.effort` rejections, mangled Swedish (`\x0f6ver`) |

Run 4-trial probes on B–D first; promote the best to a full paired arm.

### 6.2 Agent

| arm | agent | note |
|---|---|---|
| browser-use | vision | baseline |
| openhands-sdk | DOM-only | expected to fail §3.4 logo recall by construction; include to quantify the loss |
| cocoa | vision + shell | amd64-only; 15 min for 4 steps under Rosetta — **not viable on this machine** |

Metrics of interest: §3.4 only. Agents do not change §3.3 (shown above).

### 6.3 Persona pool

| arm | pool |
|---|---|
| synthetic-1000 | `generated-persona-dev-infobric-managers-1000` (baseline; 250 per tier) |
| synthetic, different seed | same config, rebuilt — tests build-to-build stability |
| real-filtered | `matraix-persona-dev-sample` filtered to construction — expect thin Swedish coverage |

Metrics of interest: tier-recall (does the pool's tier signal survive into
output?), plus pool-level checks: tier balance, the coherence audit
(`persona/scripts/audit_cohort.py`), age distribution vs target.

### 6.4 Instrument wording

Cheap to test **offline** before any browser run: call the model directly with
the rendered persona system prompt, a page summary, and the field in question.
This week that isolated a single guidance line as a 2-point level shift in
minutes, and showed no wording variant reproduces `trust`'s zero variance —
meaning `trust` is a structural problem (ratings emitted at the end of a long
browsing trajectory), not a wording one. Candidate structural fix: have the
agent record observations while browsing and score in a separate short pass.

### 6.5 Page

Homepage vs pricing vs tier page, same config. Hypothesis: pricing (real
numbers on screen) and tier pages (audience-specific copy) produce more
disagreement than the generic homepage. Not yet run.

## 7. Baseline runs already on disk

| job | page | agent | model | n | instrument |
|---|---|---|---|---|---|
| `pg-web-infobric-audit-homepage-4044ed9a` | homepage | openhands | claude-haiku-4.5 | 100 | v1 (generic basis vocab, unanchored clarity/trust) |
| `pg-web-infobric-audit-homepage-d26dac30` | homepage | browser-use | gpt-5.6-luna | 84 (76 usable) | v2 (procurement vocab, anchors, old contact line) |
| `cmp2-playwright` / `cmp2-browseruse` | homepage | both | gpt-5.6-luna | 2 + 2 | v1 — the only agent-controlled pair |
| `azure-smoke`, `azure-smoke2` | homepage | openhands | gpt-4.1-mini | 4 + 4 | v1 |
| `pg-web-infobric-audit-tier-page-1020b0e7` | tier page | browser-use | gpt-5.6-luna | 4 (3 usable) | v2 |

The two n≈80–100 runs are a ready-made (confounded) two-arm pilot for
exercising the tooling. The `partner` branch's current instrument is **v3**
(contact_likelihood line reworded, blank-page recovery); nothing has run on v3
yet.

## 8. Implementation

```
ablation/
  README.md                  this file
  instrument_health.py       job dir → one row: every metric in §3, as JSON + a printed table
  compare.py                 N job dirs → side-by-side table, deltas, Spearman on tier ranks
  offline_probe.py           direct model calls for §6.4 wording tests (no browser)
  ground_truth/<page>.json   §4
  recipes/                   paired-cohort job recipes, one per arm, fresh job names
  findings/                  one file per established finding, plain English, paper-ready
```

Order of work:

1. `instrument_health.py` over the five baseline jobs in §7. Most of the code
   exists as ad-hoc scripts from this week; consolidate it.
2. Ground-truth files for the three pages.
3. Test-retest: re-run `d26dac30`'s 84 persona ids once. Establishes the noise
   floor for every η² in this plan.
4. Model probes (§6.1 B–D), 4 trials each, homepage.
5. Full paired model arm for the winner.

## 9. Open gaps

- **Cost is untracked for browser-use.** Every cost comparison is blocked until
  harbor reports it.
- **No test-retest yet.** Every discrimination claim above is provisional.
- **`trust` is dead** on the current pipeline for a structural reason; either
  drop it from primaries or implement the browse/score split. Full reasoning,
  evidence and recommendation: `findings/trust-rating-collapse.md`.
- **`context.md` ships all four tier scenarios in every prompt** and relies on
  the persona to self-select. It works (93%) but is fragile; injecting only the
  persona's own scenario would be cleaner. Not changed mid-study.
- The 144 MB synthetic pool is gitignored. Rebuild from
  `persona/scripts/cohort_configs/infobric_managers.yaml`; note the sampler is
  not seeded, so a rebuild is a new draw (see §6.3).
