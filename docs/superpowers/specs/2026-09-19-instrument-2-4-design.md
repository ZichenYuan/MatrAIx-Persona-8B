# Instrument 2.4: wrong-fit identities, stay-or-go first, and a trust ladder

*Design note, 2026-09-19. Follows the 2.3 smoke (`ablation/findings/smoke-instrument-2-3.md`).*

## 1. What the 2.3 smoke taught

| Question | Result | Why |
|---|---|---|
| Do existing customers leave? | Yes: 27% exit, 100% go to login | The arrival note at the end of the persona prompt is read and acted on |
| Do wrong-fit visitors leave? | No: 0 of 7 | They still carry construction-sector jobs, so the first screen reads as relevant to them; the "review" framing then takes over |
| Do prospects behave as before? | Yes: scores match the 1,000-run baseline | Good: comparability holds |
| Do three trust acts spread? | No: 42 of 49 answer no / no / yes | One item costs nothing (mention to a colleague), one is out of reach on a first visit (phone number today); only "accept the claim unchecked" discriminates |

So the population fix works where the identity matches the segment, the framing still pushes
everyone to read, and the trust items need a graded cost between the two extremes.

## 2. Wrong-fit visitors get their own identities

The wrong-fit segments are built as a separate mini-pool with the cohort builder
(`persona/scripts/build_cohort.py`, config `persona/scripts/cohort_configs/infobric_wrong_fit.yaml`),
not derived from prospects. Swedish residents, no construction background
(`ind_construction: None / Some exposure`), four groups:

| Segment | Who | Why they are on infobric.com |
|---|---|---|
| Job seeker | software, sales, marketing, support, HR people; `linkedin_activity: Job seeker` | heard Infobric is hiring; wants the careers page |
| Supplier or partner | sales and marketing people at IT consultancies, recruiters, agencies, component makers | wants a name or a partner page to pitch to |
| Student or researcher | students (`demo_employment_status: Student`), 18–34 | writing an assignment about digitalisation in construction |
| Mis-click / private person | anyone outside construction, incl. healthcare, education, public sector | searched for a driving-log app for a company car (a Swedish tax need), clicked an ad, or expected another site |

Each persona carries the audit fields the verifier and report expect (`audience_group` =
"Not a target visitor", `tier` = "Not applicable", `deals_with_*` = "Not part of my job"),
plus `traffic_segment`, `visit_intent`, `infobric_familiarity` and an `arrival_note`.
`build_traffic_mix_pool.py --wrong-fit-source` then assembles the traffic-mix pool from
prospects (40%) and existing customers (45%) drawn from pilot-full, and wrong-fit (15%)
drawn from the mini-pool. Prospects stay byte-identical to the baseline.

## 3. Stay or go, decided before any review

The visit is reframed from "Review one page" to "A visit to one page". After the
self-briefing the persona opens the page, looks only at the first screen and decides
**now**: stay or go. The decision rule is written out: go if this is not what you came for,
if you cannot tell what they offer, if it is clearly for someone else, or if nothing holds
you; stay only if something on the first screen gives you a reason to read on. Going means
filling a short exit form (briefing, first-screen answers, understanding, the trust items,
next step, reason, one improvement) and saving — "that is the whole visit". The review
questions only exist for those who stay.

Why this is the right lever: 100% of 2.3 personas wrote a hesitation reason and 0% of
prospects acted on it. The current text permits leaving as an exception inside a review
job. Putting the decision first, with a rule, turns stated hesitation into a choice the
persona has to make. The risk is over-correction (prospects leaving because the text
invites it). The check is the calibration table: exit rate by segment against Quick Backs,
with prospects' scores compared to the baseline for drift.

## 4. Trust as a ladder of stakes

Keep the 1–5 rating for comparability and the claim item because it discriminates. Replace
the two extreme acts with four rungs of increasing cost, each yes/no, "this week, from your
own situation":

| Rung | Field | Cost to the persona |
|---|---|---|
| 1 | `trust_email_guide` — give your work email to get a guide or price indication | spam, being on a list |
| 2 | `trust_callback` — ask them to call you back | a sales conversation |
| 3 | `trust_demo_week` — book a 30-minute demo this week | time, colleagues seeing it |
| 4 | `trust_pilot_data` — run a pilot on your own company's live data this month | operational and data risk |
| — | `trust_claim_unchecked` — accept the page's proof claim without checking it | credulity (belief, not act) |

Derived: `trust_ladder` = number of rungs answered yes (0–4); `trust_ladder_consistent` =
no rung above a "no" is answered "yes" (a Guttman check; inconsistency is reported, not
punished). Existing customers and non-evaluators are told that answering no to all four is
expected. The report treats the ladder as the primary trust measure, the 1–5 as secondary,
and shows the claim item separately.

Expected effect: prospects spread over 0–2 (email yes for many, call-back split, demo
rarely, pilot almost never on a first visit), with visit intent and the trust-level trait
moving the count. If the ladder still compresses, the next lever is disposition promotion
into the situation block (design arm 2).

## 5. Claude 4.8 as the persona model

The Playground offers `anthropic/claude-opus-4-8` through the local Copilot gateway on
:8992. Containerised trials failed before because the agent forwarded
`ANTHROPIC_BASE_URL=http://127.0.0.1:8992`, which inside a container is the container
itself. Verified today: the gateway listens on all interfaces, a container reaches it at
`host.docker.internal:8992` (HTTP 200), it accepts the dashed model id, and it supports tool
use (browser-use needs it). Fix: the installed browser-use agent rewrites loopback hosts in
forwarded base URLs to `host.docker.internal`.

## 6. Run plan

50 personas on the homepage with `anthropic/claude-opus-4-8`, traffic-mix pool v2
stratified by segment, concurrency 4. Read: exit by segment (esp. wrong-fit), prospects'
scores vs baseline (drift check for the new framing), ladder distribution and its η² by
visit intent and trust level, and a model comparison against the 2.3 smoke on gpt-5.6-luna
(same instrument minus the framing change, so read model effects with care).
