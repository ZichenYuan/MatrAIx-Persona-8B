# Smoke of instrument 2.3: traffic mix (arm 1) and trust as three acts (arm 6)

*Homepage, job `pg-web-infobric-audit-v2-homepage-ec2e5092`, 2026-09-19 08:52–09:25 PDT, 50 personas
from `generated-persona-dev-infobric-traffic-mix` stratified by traffic segment (22 existing customers,
20 prospects, 3 job seekers, 2 mis-clicks, 1 supplier, 1 student), persona-browser-use + gpt-5.6-luna,
concurrency 4. 49 of 50 passed after one retry round (the one failure is the quit-at-step-1 quirk).
Full numbers: `ablation/baselines/homepage-smoke-2.3-ec2e5092/summary.md`.*

## Arm 1 — traffic mix: the exit rate moves, and only where it should

| Segment | n | left after first screen | next step |
|---|---:|---:|---|
| Existing customer (login/support) | 22 | **27%** | go_to_login 100%, contact likelihood 1.05 |
| Prospect | 20 | 0% | contact_sales 7, learn_more 12, come_back_later 1 |
| Wrong-fit (job seeker, mis-click, supplier, student) | 7 | 0% | learn_more / come_back_later |

- Overall exit after the first screen: **12%** (baseline 0%; partner's Quick Backs 44%).
- Existing customers behave as intended: those who left say the first screen shows a visible
  "Logga in" and that is all they need; the 73% who kept reading still ended at login. The
  arrival note at the end of the persona prompt is read and acted on (persona fidelity 100%).
- Wrong-fit visitors do not leave. Their reasons show why: they still carry construction-sector
  jobs (the pool is derived from pilot-full), so the first screen reads as relevant ("relevant to
  my rental responsibilities, but I came as a job seeker"), and the review framing then takes over.
  Real mis-clicks and job seekers are mostly not construction people. Two follow-ups: give the
  wrong-fit segments non-construction identities (a separate mini-pool), and put the stay-or-go
  decision before any review question (design arm 4).
- Prospects are unaffected by the instrument change: understanding 4.00, trust 3.00, language
  3.80, practical value 3.87 (baseline 4.01 / 3.00 / 4.00 / 3.67), so runs remain comparable.

## Arm 6 — trust as three acts: works mechanically, badly calibrated

| Act | yes |
|---|---:|
| Would type name, company and phone into the form today | 0% |
| Would accept «Betrodd av över 12 000 kunder och 450 000 användare» unchecked | 6% |
| Would mention Infobric to a colleague after one visit | 88% |

- 42 of 49 personas answer exactly no / no / yes; the 0–3 count has sd 0.33, barely more than
  the 1–5 rating (sd 0.00). One item is too hard, one too easy; the claim item discriminates.
- A whisper of the persona trait appears (Hostile 0.50, Skeptical 0.91, Verifying 1.10,
  Trusting 1.00 mean yes-count) on tiny cells; nothing the 1–5 rating ever showed.
- Recalibrate as a ladder of stakes between the extremes, keeping the claim item:
  give an email address for a guide · ask for a call-back · book a demo this week · hand over a
  phone number today. Expect the ladder to spread the count over 0–4.
- Two early exits left "recommend" unanswered; the verifier records that as unmapped (not a
  failure). Wording: "answer all three even if you leave" is in the instruction; tighten if it recurs.

## Everything else held

Clean JSON 100%, quoted wording found on the page 96–97%, primary button inspected by 88% (the
early exits skip it by design) and correct in 100%. `contact_likelihood` now spreads (sd 1.16)
purely because customers answer 1 — report it per segment, never pooled.

## Next

1. Wrong-fit identities as their own mini-pool (non-construction), then arm 4 (stay-or-go first).
2. Trust ladder (4 acts) — a 50-persona smoke is enough to see the spread.
3. Then a 200-persona homepage run per arm before pages 2–5.
