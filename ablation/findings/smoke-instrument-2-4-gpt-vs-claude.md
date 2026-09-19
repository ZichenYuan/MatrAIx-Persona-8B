# Instrument 2.4 on GPT-5.6 Luna, persona for persona against Claude Opus 4.8

*Homepage, job `pg-web-infobric-audit-v2-homepage-b63ddebd`, 2026-09-19 12:48–13:15 PDT. The same 50
personas as the Claude run (`58a824d2`; seed 42 on traffic-mix v2), on the refined instrument
(2.4 + `go_elsewhere_on_site`, softer existing-customer note, `trust_ladder_reason`). 49 of 50
finished and passed after re-verification (two verifier strictness fixes: numeric strings for
scores, `understanding` may be unknown on an exit); one quit-at-step-1 crash could not be retried
because the task files were regenerated during the run, which changes Harbor's job lock - do not
regenerate tasks while a job may still need a retry. Numbers:
`ablation/baselines/homepage-smoke-2.4-gpt-b63ddebd/summary.md`; report: `jobs/…b63ddebd/report/partner_report.md`.*

## Framing: stay-or-go does not push prospects out, on either model

| Segment | GPT-5.6 (this run) | Claude 4.8 |
|---|---|---|
| Prospects left | 0 of 20 | 1 of 20 |
| Existing customers left | 21 of 22 (softer note: "up to you") | 23 of 23 (note told them to go) |
| Wrong-fit left | 6 of 7 | 6 of 7 |
| Same exit decision, same persona | 47 of 49 | — |

- The stay-or-go rule is not an over-correction: prospects stay under it with both models, and
  their six scores match the 834-trial baseline (understanding 4.05, trust 3.00, practical value
  3.65 vs 4.01 / 3.00 / 3.67). The framing changes what non-prospects do, not what prospects say.
- Customers go straight to login by their own choice once the note stops telling them to
  (21 of 22). That was the persona, not the script.
- `go_elsewhere_on_site` separates bounces from journeys: job seekers now route to careers
  (2 of 3), mis-clicks and the supplier bounce (4). **Bounced = 4 of 49 (8%)** is the number
  to set beside Quick Backs; the previous 60% "exit" was mostly routing.

## Trust ladder: consistent, monotone, and it separates situations

| Prospects (n=20) | GPT-5.6 | Claude 4.8 |
|---|---:|---:|
| work email for a guide | 20 | 13 |
| call-back | 8 | 4 |
| demo this week | 0 | 1 |
| pilot on own data | 0 | 0 |
| rungs accepted, mean (sd) | 1.40 (0.49) | 0.90 (0.70) |
| inconsistent ladders | 0 | 1 |
| accept the proof claim unchecked | 0 | 8 |

- η² of rungs by visit intent: **0.89** on GPT (specific problem: call-back 62%; exploring: 0%),
  0.64 on Claude. The ladder reads the situation the 1–5 trust rating never did (trust sd 0.00
  on GPT again).
- Model difference on identical wording: GPT climbs one rung higher on average, never takes the
  claim at face value; Claude is more sceptical of commitments and more credulous on the claim.
  Same persona, same next step in 30 of 49 cases; GPT prospects choose contact sales 14 of 20,
  Claude 4 of 20. Report model as an ablation factor, never pool the two.
- `trust_ladder_reason` delivers the advice content directly: "a named reference from a similar
  small Swedish contractor, a price range, and a clear explanation of GPS/data handling and rollout
  effort"; Fortnox and finance integrations come up by name. The report's trust section (§3c) is
  now built from these.

## What the report can tell the partner about trust (homepage)

Trust is earned to the level of "send me something" and stops at "talk to me": every prospect
would give an email for a guide, 40% would take a call-back, none would book a demo or pilot.
What moves the next step is concrete and repeated: a named comparable reference, an indicative
price range, integration facts (Fortnox, payroll, finance), data-handling in plain words, setup
effort, and a low-risk walkthrough. The doubted wording is the same across models: «Betrodd av
över 12 000 kunder och 450 000 användare» (believed but unverified), «En ledande
digitaliseringspartner…», «marknadens bredaste utbud», «Vi bidrar till att bygga en bättre värld».

## Next

- 200 prospects-heavy run per model on the homepage for partner-facing numbers (visitor kinds
  with n≥20), then pages 2–5 with the same instrument.
- Keep the segment mix as an explicit assumption in the report; the bounced rate (8%) vs Quick
  Backs (44%) gap remains a population question the analytics cannot settle without a
  new-user filter.
