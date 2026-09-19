# Why nobody leaves, and why three scales do not spread

*Homepage audit v2.2, job `pg-web-infobric-audit-v2-homepage-3fffd213`, 803 passed visits
analysed on 2026-09-19 while the 1,000-persona run was still finishing. Numbers below come
from `quality.json`, the persona YAMLs, and `ablation/ground_truth/analytics_90d.json`.*

## 1. The two gaps

| What we measured | Simulation | Real traffic (partner analytics, 90 days) |
|---|---|---|
| Left after the first screen | **0 of 803** | 44% Quick Backs (10,058 of 22,983 sessions) |
| Trust (1–5) | 3.00 for everyone, sd 0.00 (post-hoc: 2.99, sd 0.10) | — |
| Understanding, language relevance (1–5) | 4 for 99% / 94% (sd 0.12 / 0.24) | — |

Practical value, next-step confidence and ease, button match, contact likelihood, next step,
and "needed before going further" do spread, and contact likelihood tracks the persona's
visit intent strongly (specific problem → 67% contact sales; exploring → 9%). So the
instrument is not dead; two specific parts of it are.

## 2. Gap A — nobody leaves. Five causes, with evidence

**A1. We simulate a different population from the one the analytics measure.** Every
persona in the pool is a Swedish construction-sector prospect whose job touches personnel,
machines or vehicles, and the homepage's first screen says exactly those three words
("Vi samlar hanteringen av personal, maskiner och fordon…"). 100% of personas therefore find
the first screen relevant. Real homepage sessions are not like that: 51% contain a *login*
event (existing customers heading to the product), 43% are returning users, and Quick Backs
also count mis-clicks from ads and search, job seekers, students and suppliers. If every
Quick Back happened in a non-login session, 89% of those sessions bounced; if they are
spread evenly, 44%. Either way we are comparing attentive prospects with mixed traffic.
This is the largest cause and it is a design choice, not a model failure.

**A2. The visit is framed as a review.** The instruction is titled "Review one page of a
supplier's website" and leaving is allowed as an exception inside that job. Personas do the
job: 100% wrote a "what would make you hesitate or leave" reason, 0% left, and 0% of
first-screen reasons contain a doubt word (hesitate, unsure, vague, generic…). Stated
hesitation never becomes revealed behaviour because the task never asks for the decision
*before* the review starts.

**A3. Time costs nothing.** Real visitors spend 11 seconds on average and scroll 35% of the
page. Personas have no clock, no competing tab and no fatigue; they use a median of 6
browser steps and read everything.

**A4. Everything rewards finishing.** Forty answer fields, "never end without saving", the
agent framework's own drive to complete, and a verifier that fails an unsaved audit. The
early-exit branch is permitted, but every other signal says "finish".

**A5. The traits that would make someone leave never reach the behaviour.** The pool carries
`trust_level` (Skeptical 34%, Verifying 31%, Trusting 30%, Hostile 5%), `emotional_state`
(Frustrated 9%), `time_pressure` (Emergency 3%). Their effect on trust, contact likelihood
and next step is zero (η² = 0.000–0.006 in-browse). They sit in a ~24,000-character identity
block; the one field that *is* restated in the persona's own self-briefing, `visit_intent`,
moves the next step by 58 percentage points. What the persona says about itself in the
situation block acts; what is buried in the identity block does not.

## 3. Gap B — three scales do not spread. Four causes

**B1. Rating at the end of a long trajectory** (see `trust-rating-collapse.md`). Re-scoring
after the visit restores spread on understanding (sd 0.10 → 0.42) and language relevance
(0.10 → 0.50, with a tier signal η² = 0.23), but not on trust.

**B2. The trust anchor is a script.** Anchor 3 reads "a credible company, but the claims are
unproven for my case". For a first-time visitor of a homepage that shows logos and numbers
but no references, that sentence is simply true, so everyone picks it. The post-hoc "why"
texts echo it: 100% say "established/credible", 45% say "unproven". The scale measures a
property of the page (no proof for my case), not a disposition of the persona.

**B3. Dispositions do not reach the rating** (A5 again): Hostile and Skeptical personas rate
trust 3.00 like Trusting ones.

**B4. One stimulus for everyone.** All 1,000 personas see the same first screen and the same
page, and the page is competent. Between-persona variance on "did you understand it" may be
genuinely small; spread appears when there is a contrast — a worse page, a variant, or a
second page to compare with.

**B5. A 5-point scale with three worded anchors compresses to 3–4.** Nobody used 1 or 5 on
trust, and 1–2 are unused on every dimension.

## 4. Design changes, ranked. Each one is an ablation arm

| # | Change | Fixes | What to measure | Cost |
|---|---|---|---|---|
| 1 | **Traffic-mix population.** Build the simulated population from the analytics, not from the brief alone: a share of existing customers looking for login, a share of wrong-fit visitors (job seekers, private persons, suppliers, students, mis-clicks from an ad), and the current prospects. Report exit rate per segment and compare the *prospect* segment with analytics for new, non-login users where available. | A1 | exit rate by segment vs Quick Backs; stays 0 for prospects? | Low: a 200-persona non-prospect sub-pool, one run |
| 2 | **Promote dispositions into the situation block.** Put `trust_level`, `time_pressure`, `emotional_state`, `prior_context` into the audit's situation text and require the self-briefing to restate them ("I generally do not take vendor claims at face value"; "I have five minutes"). | A5, B3 | η² of trust by `trust_level` (now 0.000; target > 0.06); exit rate among Hostile/Frustrated/Emergency | Low: template + self-briefing wording, 200 personas |
| 3 | **Skim / time-boxed arm.** First screen only: "you landed here the way people land on pages; leaving is the default unless something holds you; decide in seconds", 2 browser steps, ratings limited to understanding and would-continue. The generator already supports `--variants skim`; the variant file `pages/variants/skim.md` still has to be written. | A2, A3 | exit rate vs full arm on the same personas | Low: 200–300 personas, ~1 min each |
| 4 | **Ask for the leave decision first, then review.** Retitle the task as a visit, put "stay or go?" before any review question, and make the questionnaire conditional on staying. Removes the completion pressure on the exit choice; the verifier already accepts early exits. | A2, A4 | exit rate; stated-vs-revealed gap | Medium: instruction rewrite |
| 5 | **Comparative and forced-choice measures instead of absolute 1–5.** Rank the six dimensions best→worst for this page; allocate ten points across "what this page most needs"; pairwise page comparisons (homepage vs Fleet). Spread comes from contrast, and behavioural items (next step, needed-before-going-further, missing information) already spread and should carry more weight in the partner report. | B4, B5 | dispersion, η² by visitor kind, test–retest | Low–medium: instrument fields + verifier |
| 6 | **Replace the trust scale with three concrete yes/no acts** with stakes: "Would you enter your company details in the form today?", "Would you accept '12 000 kunder' without checking?", "Would you recommend this to a colleague after one visit?" Aggregate to a score. Concrete acts vary with disposition; a truth-anchor does not. | B2 | agreement with `trust_level`; spread | Low |
| 7 | **Repeat visits (same persona × 3).** Separates noise from signal; needed for the paper's reliability section regardless. | B (all) | test–retest, intra-class correlation | Medium: 3× cost on a 200 subset |
| 8 | **Stimulus contrast (sensitivity check).** Same pool on a deliberately weakened copy of the page (e.g. the customer-proof line removed, or a generic hero), served locally. If scores do not move, the instrument cannot detect page differences at all. | B4 | score deltas per dimension | Medium: a static mirror of the page |

## 5. What to run first

Arms 1, 2 and 3 on the homepage, 200 personas each (about two hours each at concurrency 4,
roughly the cost of 200 trials each). Together they answer the three questions the partner
will ask: *is the 0% exit a population effect or a simulation effect* (1 vs 3), *can the
simulation express a sceptical visitor at all* (2), and *does time pressure change the
outcome* (3). Decide on 4–6 after that, before running pages 2–5, so the five pages are run
with one instrument.

## 6. What can be reported honestly today

- Exit rate as "0% among attentive prospects", side by side with Quick Backs and the
  population caveat; the gap is itself a calibration result.
- Trust through *what visitors need before going further* (96% references first) and *which
  claims they wanted proof for*, not through the score.
- Spread and audience differences where they exist: practical value, next step, contact
  likelihood by visit intent, language relevance by tier (post-hoc).
