# Finding 1: the trust rating collapses to a single value

- **Status:** established on one page, one run; not yet repeated
- **Date:** 2026-09-16 / 17
- **Branch:** `ablation` (builds on `partner`)
- **Main run:** `jobs/pg-web-infobric-audit-homepage-d26dac30` (browser-use, gpt-5.6-luna, 84 trials, 76 usable)

## In one paragraph

We asked 76 different simulated people to rate, from 1 to 7, how much they
trust a supplier after reading its homepage. Every one of them answered 5.
We tested each possible cause on its own — the wording, the size of the
questionnaire, the persona, whether the persona reached the model, the
browsing agent, the model — and none of them produced a constant. Only the
real pipeline did. The difference is *where* the question is asked: at the end
of a long browsing session whose content is huge and identical for everyone,
while the only thing that could make the answer personal sits far back at the
start. Asking the same question in a separate short pass, with the persona,
its situation, and the agent's notes close together, brings the variation
back. This matters for the paper because it is not a wording problem and no
wording fix can solve it.

## What we wanted to measure

Each persona is a Swedish construction professional from one of four audience
tiers (main contractor, subcontractor, developer, rental company). Each reads
the Infobric homepage inside a real browser and fills in a 17-field audit,
including four ratings from 1 to 7: `clarity`, `relevance`, `trust`, and
`contact_likelihood`. The report groups the ratings by tier so the website
owner can see how each audience reacts.

For this to work, different people must give different numbers.

## What we saw

| rating | spread (sd) | values used | share of variance explained by tier (η²) |
|---|---|---|---|
| `contact_likelihood` | 0.41 | 3–4 | 0.27 |
| `clarity` | 0.31 | 4–6 | 0.14 |
| `relevance` | 0.26 | 5–7 | 0.11 |
| `trust` | **0.00** | **5 only** | **0.00** |

*sd* is the standard deviation: how far the answers spread around their
average. 0.00 means they were all the same. *η²* (eta squared) is the share of
the total variation that is explained by which tier the persona belongs to;
0.27 means tier explains 27% of the differences in `contact_likelihood`.

Three of the four ratings are compressed but alive. `trust` is a constant.

An earlier run of the same page with a different model and agent
(`…-4044ed9a`, claude-haiku-4.5, playwright, 100 trials) had `trust` sd 0.55
with tier averages between 5.04 and 5.27 — narrow, but not dead.

## Ruling out the obvious causes

Each test below calls the model directly, outside the browsing pipeline, so
one thing changes at a time.

| suspect | test | result | verdict |
|---|---|---|---|
| The wording of the question | Same page summary, four tier personas, three wordings: the original bare `<1-7>`, our anchored version, a third variant | All three gave answers spread over 4–5 | not the cause |
| Asking 17 fields at once | Full 17-field rubric vs `trust` alone | Full rubric gave *more* spread, not less | not the cause |
| The persona text | Fed the real rendered persona (about 22,000 characters) instead of a one-line description | Spread over 4–5 | not the cause |
| Persona not reaching the agent | Checked whether each audit's free text reflects the *assigned* tier | 93% match, against 25% if random | persona gets through |
| The browsing agent | Playwright vs browser-use, same model, same instrument (`cmp2-*` jobs) | Both gave `trust` = 5, 5 | not the cause |
| The model | gpt-5.6-luna compresses ranges more than claude-haiku | But luna varies fine outside the pipeline | makes it worse; not the cause on its own |

Every ingredient, alone or together, outside the pipeline, varies. Only the
real pipeline gives a constant. So the cause is the pipeline's shape.

## What is different about the real pipeline

The browsing agent runs a loop. In order, the model reads:

1. the persona identity block (about 22,000 characters, at the very start),
2. the task instruction and the situation text (`context.md`),
3. then several browsing steps — each one a screenshot plus the page's text
   tree, tens of thousands of tokens, **identical for every persona because it
   is the same page** — plus the agent framework's own messages,
4. and only then does it write the JSON with the ratings.

So at the moment it writes `"trust":`, the nearest and largest thing in its
context is the same for everyone, and the only thing that could make the
answer personal is far back at the start.

## Our explanation

Picture a questionnaire handed out at the end of a two-hour factory tour.
Everyone just walked the same shiny floor, so "would you trust this company?"
gets the same polite answer from all of them. The line in their briefing pack
saying "you were burned by a supplier last year" was on page one, two hours
ago. But "will you call them next week?" still varies, because the briefing
also said "your 40-person site starts next month" — a concrete deadline is
easy to hold on to.

That is the pattern in the data. `contact_likelihood` survives because the
situation text gives it a concrete hook: a legal deadline, a project starting.
`trust` has no such hook — nothing in the situation says how trusting the
person is — so the only pull away from a default answer is the diffuse
identity block at the start, and that gets buried. With nothing pulling it,
the model gives the default: a professional page with Skanska and NCC logos
earns a polite 5 from everyone.

Two results support this specific mechanism. We re-scored the same 76 audits
outside the browse, giving the model the persona plus the agent's own short
notes about the page:

| re-scoring condition | `trust` sd | `trust` η² | `contact` η² | `contact` values used |
|---|---|---|---|---|
| in the pipeline (original) | 0.00 | 0.000 | 0.27 | 3–4 |
| outside, **without** the situation text | 0.30 | 0.005 | 0.07 | — |
| outside, **with** the situation text | 0.36 | 0.09 | **0.40** | **2–6** |

Without the situation text, variation returns but has nothing to do with tier.
With it, tier signal appears, and `contact_likelihood` becomes much stronger
than it ever was in the pipeline. So the tier signal for these ratings lives
in the situation text, and in the pipeline the situation text is what gets
drowned.

This is also why our earlier attempt to fix `trust` by adding scale anchors
could not work: anchors change wording, and the wording is not the problem.

## Why some ratings survive and trust does not

The ratings that survive are the ones the situation text gives a reason to
move. `contact_likelihood` asks about "your next week" and the situation
supplies a deadline. `clarity` asks "what this would do for you" and the
situation supplies a need. `trust` asks about a disposition the situation
never mentions.

A supporting observation: `clarity` gets *worse* when scored outside the
browse (η² 0.14 → 0.03). It is a judgement about the page as seen, so it
belongs in the browse. The judgements that improve outside the browse are the
ones about the person.

## Another possible explanation

Maybe after actually seeing the page, all personas honestly agree on 5,
because the homepage gives everyone identical trust cues — and the variation
we recover outside the browse is partly the model guessing without having
looked. We cannot cleanly separate "the persona got drowned" from "everyone
genuinely agrees."

Two things make the first reading more likely. Seventy-six people landing on
the identical digit is implausible even under true agreement. And even in the
best condition, trust's tier effect is only marginal (F about 2.4, just under
the usual 2.73 cut-off), which fits "trust really does not differ much by tier
on this page" — but not zero.

Either way the practical conclusion is the same: a constant cannot be compared
across anything, and trust as a single number is the least reliable output of
this method.

## What this means

- The report's "Trust (1–7) by tier" chart is one flat bar, and it reads as a
  finding when it is an artifact.
- Any comparison of `trust` across models, agents, or pools would be comparing
  constants.
- More generally: **ratings collected at the end of a long, uniform
  trajectory lose the persona.** This applies to any simulation that has an
  agent browse first and judge afterwards.

## What we recommend

1. Stop treating `trust` 1–7 as a headline. Report it as descriptive only,
   with its sd shown.
2. Score the person-judgement fields (`trust`, `contact_likelihood`) in a
   separate short pass after the browse, giving the model the persona, the
   situation text, and the agent's recorded observations. Keep the page
   judgements (`clarity`) in the browse.
3. Measure trust through what the method does capture well: which trust cues
   were noticed (`trust_signals_noticed`, checkable against the real page),
   what is missing (`missing_info`), what would be needed before proceeding
   (a new categorical `trust_action`: share data now / need references first /
   need a pilot first / would not proceed), and the behavioural consequence
   (`contact_likelihood`). In the re-scoring run, `trust_action` split cleanly
   by tier — developers wanted references (17/17), rental companies and
   subcontractors wanted to pilot it (about 55%) — which is directly
   actionable for the website owner.

## Limits of this finding

- One page (the homepage), one model (gpt-5.6-luna), one browsing agent
  (browser-use), one run of 76.
- No test–retest yet, so we do not know the noise floor for any η² here.
- The re-scoring tests are paired (same 76 personas both ways), which is why
  we trust the direction of the effects at this size; the exact numbers are
  provisional.
- The mechanism is inferred from elimination plus the re-scoring reversal. We
  have not measured what the model attends to directly.

## How to reproduce

- Pipeline data: `jobs/pg-web-infobric-audit-homepage-d26dac30/*/artifacts/**/page_audit.json`
  with each trial's `persona_meta.json` → persona YAML → `tier:`.
- Baseline with a different model/agent: `jobs/pg-web-infobric-audit-homepage-4044ed9a`.
- Agent-controlled pair: `jobs/cmp2-playwright`, `jobs/cmp2-browseruse`.
- The offline wording, rubric-size, persona, and re-scoring tests were run as
  ad-hoc scripts against the Azure endpoint during the 2026-09-16 session;
  their planned homes are `ablation/offline_probe.py` and
  `ablation/rescore.py` (see `ablation/README.md` §8). The persona system
  prompt is rendered with `agents.persona.loader.load_persona` and
  `agents.persona.templating.render_persona_template`.

## Terms used

- **persona** — the simulated person: a YAML file of about 1,290 attributes,
  rendered into an identity text the model reads as who it is.
- **situation text / `context.md`** — the short scenario given with the task
  ("next month you take over a 40-person site…"), one per tier, all four
  shipped in every prompt with the persona picking its own.
- **in the pipeline / in-pipeline** — produced by the browsing agent at the
  end of its browse.
- **post-hoc / re-scoring** — produced afterwards by a separate model call
  that is given the persona, the situation, and the agent's notes.
- **sd** — standard deviation, how spread out the answers are.
- **η² (eta squared)** — share of variation explained by tier, 0 to 1.
- **F** — the test statistic behind η²; above about 2.73 (for four tiers and
  76 people) the tier effect is unlikely to be chance.
