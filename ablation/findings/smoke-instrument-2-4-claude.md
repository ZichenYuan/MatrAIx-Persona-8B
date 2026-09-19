# Smoke of instrument 2.4 on Claude Opus 4.8: wrong-fit identities, stay-or-go first, trust ladder

*Homepage, job `pg-web-infobric-audit-v2-homepage-58a824d2`, 2026-09-19 10:20–10:47 PDT, 50 personas
from traffic-mix v2 (23 existing customers, 20 prospects, 7 wrong-fit from the non-construction
mini-pool), persona-browser-use + `anthropic/claude-opus-4-8` via the local gateway, concurrency 4.
50 of 50 passed, no retries. Numbers: `ablation/baselines/homepage-smoke-2.4-claude-58a824d2/summary.md`.
Compared with the 2.3 smoke on gpt-5.6-luna (`ec2e5092`) and the 834-trial baseline (2.2, gpt-5.6-luna).*

## Exit after the first screen, by segment

| Segment | n | left | next step |
|---|---:|---:|---|
| Existing customer | 23 | **100%** | go_to_login 23 |
| Wrong-fit (job seeker, mis-click, supplier, student) | 7 | **86%** | leave 7 (the student read first, then left) |
| Prospect | 20 | 5% | learn_more 14, contact_sales 4, book_demo 1, leave 1 |
| All | 50 | 60% | — |

- The two fixes land: wrong-fit visitors with their own identities leave (0 of 7 in 2.3 → 6 of 7),
  and the stay-or-go rule turns the customers' 27% into 100%. Prospects still stay (1 of 20).
- 60% overall against 44% Quick Backs: the simulated mix is now *more* forgiving than real
  traffic among prospects and *less* among customers. The pooled rate is driven by the assumed
  segment shares (45% customers), so the comparison has to be per segment; the partner's
  analytics cannot split Quick Backs by visitor kind, which is the remaining calibration gap.

## Trust ladder

| Rung | all 50 | prospects (20) | specific problem (13) | exploring (7) |
|---|---:|---:|---:|---:|
| work email for a guide | 26% | 65% | 85% | 29% |
| call-back | 8% | 20% | 31% | 0% |
| demo this week | 2% | 5% | 8% | 0% |
| pilot on own data | 0% | 0% | 0% | 0% |
| accept the claim unchecked (belief) | 64% | 40% | 46% | 29% |

- Rungs accepted: 0 → 37, 1 → 8, 2 → 5 (mean 0.36, sd 0.66); one inconsistent ladder in 50.
  η² by visit intent **0.64**, by traffic segment 0.45, by visitor kind 0.18. The ladder does
  what the three acts could not: it separates situations (a specific problem today vs
  exploring) and it is monotone. Non-evaluators answer 0, as instructed.
- Ceiling is fine, floor is crowded: the first rung is the only one prospects climb readily.
  Keep the ladder; consider a rung between "email" and "call-back" (e.g. "reply to their
  follow-up email") only if 0/1 stays the whole story at n=200.

## Model effect (prospects only, same instrument family)

| Measure | Claude 4.8 (2.4) | GPT-5.6 Luna (2.3) | baseline GPT (2.2, n=785) |
|---|---:|---:|---:|
| understanding | 3.90 (sd 0.30) | 4.00 (0.00) | 4.01 |
| language relevance | 3.60 (0.58) | 3.85 (0.36) | 4.00 |
| practical value | 3.05 (0.50) | 3.75 (0.43) | 3.67 |
| trust (1–5) | 3.05 (0.22) | 3.00 (0.00) | 3.00 |
| next-step confidence | 3.20 (0.51) | 4.00 (0.00) | 3.88 |
| contact likelihood | 2.75 (0.77) | 3.35 (0.48) | 2.83 |
| accept claim unchecked (all segments) | 64% | 6% | — |
| failed trials | 0 of 50 | 7 of 50 (quit at step 1) | ~6% |

- Claude is harsher and more varied on every scale, gives fewer "contact sales" (4 vs 7),
  and never quits without saving. GPT compresses to the polite 4 and the anchor 3.
- The claim item flips: Claude takes «Betrodd av över 12 000 kunder…» at face value 64% of
  the time, GPT 6%. Either a reading difference ("would you accept" as "is it plausible") or a
  real credulity difference; the paper should report it as a model ablation result and the
  wording should say "without checking it, would you repeat it to a colleague as a fact".
- Caveat: the 2.4 framing has not been run on GPT, so "prospects still stay" under the
  stay-or-go rule is a Claude result until a GPT 2.4 run exists.

## Everything else

Clean JSON 100%, persona fidelity 100% (incl. the new arrival reasons), quotes found on the
page 97–99%, primary button inspected by the 40% who stayed (100% correct). 27 minutes for 50.

## Next

1. GPT-5.6 Luna on instrument 2.4, 50 personas: isolates the framing effect from the model.
2. Then 200 per model on the homepage; report exits per segment, ladder by intent, claim item
   by model. Ask the partner only if they can split Quick Backs by new vs returning users
   (they may already have it in Clarity); otherwise compare prospects to new-user engagement.
