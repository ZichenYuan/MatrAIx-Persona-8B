# A visit to one page of a supplier's website

You are about to land on one page of Infobric's website, as yourself, in your own job
and situation. Treat the page as the first thing you have ever seen from this company:
do not assume you have read any other page. Most people leave most pages within seconds.
This visit has the same rule: you stay only if the first screen gives you a reason to.

## Page brief

- **page_id:** `homepage`
- **Page to review:** https://infobric.com/se/
- **What this page is for:** the company's front page — a broad overview meant to tell a
  first-time visitor what Infobric is, what kinds of business problems it helps with, and
  whether it could be relevant to their business.
- **Primary next-step button to inspect (step 4):** the site's main contact or demo
  button — the one that leads to contacting the company or booking a demonstration,
  usually in the top navigation or in the first screen. Click it once and describe what
  follows. Links to individual products, solutions or audience pages are ordinary
  navigation, not the next step; do not follow them.
- **`next_step` options on this page:** `contact_sales`, `book_demo`, `learn_more`,
  `come_back_later`, `go_to_login`, `leave`.
- **Proof claim for the three `trust_*` questions:** «Betrodd av över 12 000 kunder och 450 000 användare»

The site is in Swedish. Read it in Swedish; write your answers in English. When you quote
wording from the page, quote it exactly as written, in Swedish.

## How to do the visit, in this order

**1. Before you open the page — brief yourself.** In two or three sentences, as yourself:
who you are and what you do, what in your day-to-day work is relevant to a page like this,
why you are looking at it today, and what (if anything) you already know about Infobric.
Take the reason for today's visit from your own profile, not from the page. Your profile
says why you are on this site today: you have a specific problem to solve right now, you
are exploring ways to improve operations, your company already uses Infobric and you came
to log in or reach support, or you are here for some other reason (a job, selling to them,
a school assignment, a mis-click from a search result or an ad). If you did not come to
evaluate a supplier, say so plainly and behave accordingly. Write this down first; it goes
in `self_briefing`.

**2. Open the page. Look only at the first screen — what is visible without scrolling —
and decide now: stay or go.** Answer the three first-screen questions (what you think this
company or product is; whether it matches what you came for; whether you would keep
reading). Then decide the way you would in real life:

- **Go** if this is not what you came for, if you cannot tell what they offer, if it is
  clearly written for someone else, or if nothing on the first screen holds you.
- **Stay** only if something on the first screen gives you a reason to read on.

**If you go, that is the whole visit.** Set `left_early` to `true`, fill in the exit form —
`self_briefing`, `arrived_with`, the three first-screen fields, `understanding`, the five
`trust_*` questions, `next_step` (usually `leave`, `go_to_login` or `come_back_later`),
`basis_primary`, `trust_action`, `contact_likelihood`, `reason`, and
`improvement_suggestion` (what on the first screen would have kept you) — put `unknown`
(or an empty list) in everything else, save the file, and stop. Do not read further.
Leaving is a real outcome, not a failure.

**3. If you stayed: read the whole page.** Then answer the page questions. For anything
you point to, quote the exact wording and say where on the page it sits — `top` (visible
before scrolling), `middle`, or `bottom`.

**4. If you stayed: click the page's primary next-step button once** — the one named in
the page brief. Look at what appears: a form, a page, a chat, a calendar. Describe what it
actually asks of you and whether it matches what the button led you to expect. **Do not
fill in or submit anything, do not log in, do not book anything.** Then go no further. If
the button leads somewhere you cannot see or the page fails to load, say so and mark the
related answers `unknown`. Do not open any other page.

**5. Decide what you would actually do next, then save your answers.**

Save to `/app/output/page_audit.json`:

```json
{
  "self_briefing": "<2-3 sentences, step 1>",
  "arrived_with": "<one of: specific_problem, exploring, existing_customer, other_reason — the reason for today's visit from your own profile; write only the option, no explanation>",

  "first_screen_takeaway": "<from the first screen only: what you think this company or product does, in your words>",
  "would_continue": "<yes or no — would you keep reading after the first screen>",
  "would_continue_reason": "<why, naming what on the first screen decided it>",
  "left_early": <true or false — true if you went after the first screen and did not read on>,

  "what_it_does": "<after reading everything: what this company or product does, for whom, in your words>",
  "problems_recognised": ["<your own work problems that this page speaks to, one per entry — empty list if none>"],
  "language_felt_familiar": ["<exact quoted phrases or examples that sounded like your world>"],
  "language_felt_off": ["<exact quoted phrases that felt written for someone else, or irrelevant to you>"],
  "claims_credible": ["<exact quoted claims you found believable>"],
  "claims_need_proof": ["<exact quoted claims that need explanation or evidence before you would believe them>"],
  "confusing_or_missing": [
    {"what": "<the thing, quoting wording if there is any>", "where": "<top | middle | bottom>", "kind": "<confusing | missing | unconvincing | irrelevant>"}
  ],
  "strongest_element": "<the one thing that worked best for you — name the actual element and quote it if it has wording>",
  "strongest_position": "<top | middle | bottom>",
  "weakest_element": "<the one thing that worked worst for you — name the actual element>",
  "weakest_position": "<top | middle | bottom>",
  "hesitate_or_leave_reason": "<what on this page would make you hesitate or leave, if anything>",

  "understanding": <1-5>,
  "language_relevance": <1-5>,
  "practical_value": <1-5>,
  "trust": <1-5>,
  "trust_email_guide": "<yes or no: would you give your work email address to get a guide or price indication from them this week?>",
  "trust_callback": "<yes or no: would you ask them to call you back this week?>",
  "trust_demo_week": "<yes or no: would you book a 30-minute demo with them this week?>",
  "trust_pilot_data": "<yes or no: would you run a pilot on your own company's live data this month?>",
  "trust_claim_unchecked": "<yes or no: would you accept the proof claim named in the page brief as true without checking it anywhere else?>",
  "next_step_confidence": <1-5>,
  "next_step_ease": <1-5, or "unknown" if you did not inspect the button>,

  "primary_cta_seen": "<the exact label of the primary next-step button as written on the page>",
  "cta_expectation": "<before clicking: what you expected to happen>",
  "cta_inspected": <true or false>,
  "cta_page_url": "<the URL after clicking, or \"unknown\">",
  "cta_reality": "<what actually appeared and what it asks of you, or \"unknown\">",
  "form_asks_for": ["<each thing a form asks you to provide — empty list if there was no form or you did not inspect>"],
  "cta_match": <1-5, how well what followed matched the expectation, or "unknown">,

  "next_step": "<what you would actually do now — one of the options listed in the page brief>",
  "basis_primary": "<the main thing driving that — one of: legal_compliance, consolidation, price, integrations, ease_of_rollout, proof_references, support, features, fit, other>",
  "trust_action": "<what you would need before going further — one of: share_data_now, need_references_first, need_pilot_first, would_not_proceed>",
  "contact_likelihood": <1-5, how likely you are to contact this supplier within the next week>,
  "missing_info": ["<zero or more of: price, integrations, hardware, setup_time, references, data_privacy, contract_terms>"],
  "reason": "<why you chose that next step, grounded in what you saw and your own situation>",
  "improvement_suggestion": "<the single change to this page that would most move you toward the next step, in your own words>",
  "improvement_check": "<how the site owner could tell whether that change worked — what would be different in how visitors like you behave>",
  "retain": "<what on this page already works well for you and should be kept>"
}
```

## The 1–5 scales

Use the whole range. 3 means genuinely middling, not a polite default. Anchor each score
to real behaviour:

- **understanding** — 1: I still could not say what they sell. 3: I know the category, but
  not what it would do for me. 5: I could explain to a colleague what it does and for whom.
- **language_relevance** — 1: written for someone else; nothing from my world. 3: general
  business language with some familiar examples. 5: my situations and my words; I
  recognised my own problems.
- **practical_value** — 1: no idea what would change in my day. 3: a plausible benefit,
  not concrete. 5: I can name what would get easier or cheaper for me.
- **trust** — 1: I would not share my data with them. 3: a credible company, but the
  claims are unproven for my case. 5: I would put my own operation on it without asking
  for references.
- **next_step_confidence** — 1: no idea what I should do next or what would happen.
  3: I see a button but not what follows. 5: I know exactly what happens after clicking,
  and it suits me.
- **next_step_ease** — 1: the step is unclear, demanding or off-putting. 3: doable, with
  some friction or uncertainty. 5: quick and obvious, nothing in the way. `unknown` if you
  did not inspect it.
- **cta_match** — 1: nothing like what I expected. 3: partly. 5: exactly what I expected.
- **contact_likelihood** is about your own next week, not how good the page is. Contacting
  them costs you a sales conversation and follow-up calls; weigh that against how pressing
  your situation actually is. Someone with a deadline and no system may well reach out;
  someone with time and a working setup may not. Let your own situation decide.

## The five `trust_*` questions

They are about what you would actually do, not about how the page looks. The first four
are a ladder of commitments, each costing you more than the one before: your email (spam,
being on a list), a call-back (a sales conversation), a demo (half an hour, colleagues
seeing it), a pilot (your own operation and data). Say `yes` only to what you would really
do this week or this month, given how pressing your situation is and how you usually treat
suppliers' claims. Someone who came to log in, or who did not come to evaluate a supplier
at all, will usually answer `no` to all four — that is the correct answer for them. The
fifth question is about belief: would you take the named proof claim at face value.
Answer all five on an early exit too, from what you saw on the first screen.

## Requirements

- Quote wording exactly as it appears on the page, in Swedish, inside the JSON string.
  Do not paraphrase a quote. Lists of quotes may be empty, but must not contain invented
  text.
- On an early exit (`left_early: true`) the required answers are the exit form listed in
  step 2. Everything else may be `unknown` or an empty list. Do not invent answers about
  parts of the page you did not read.
- `arrived_with` reflects your profile, not the page. If you are exploring, say
  `exploring` even if the page shows problems you could have; say `specific_problem`
  only if you actually came with one today; `existing_customer` if your company already
  uses Infobric and you came to log in or for support; `other_reason` if you are not here
  to evaluate a supplier at all (a job, selling to them, research, a mis-click).
- `next_step` must be one of the options listed in the page brief for this page, and must
  be what you would actually do today. `learn_more`, `come_back_later` and `leave` are
  all valid, and `leave` is right if the page does not give you what you need.
- `basis_primary` is the single thing that actually drives your next step. Use `fit` only
  when no more specific reason applies.
- `trust_action` is the concrete thing you would need before going further.
  `share_data_now` means you would sign up or hand over details today.
- `improvement_suggestion` is advice to the page's owner: specific, and tied to what you
  saw. `improvement_check` is how they would know it worked.
- Anything you did not inspect is `unknown`, not a guess.
- `missing_info` and enumerated fields must use only the listed values, spelled exactly.
- **Save the file with your file-writing tool** (for example `write_file`) to exactly
  `/app/output/page_audit.json`, then read it back and check it is complete, valid JSON.
  Do not try to run Python or shell commands to write it — you may not have them, and you
  do not need them.
- **Never end without saving the file.** Nothing ends this run except your own final
  action — if you ever think the run has already ended, it has not: save the file.
- If your file tool adjusts or auto-corrects the save path (for example into a sandbox
  subdirectory), that is expected and acceptable — the saved file is still correct. Do
  **not** treat a path adjustment as a failure.
- If a page looks blank or empty after you navigate, that is almost always a slow render,
  not a broken site. Wait a moment and reload it, and try once more before concluding
  anything. Do not end the task by reporting an empty page — the site is known to be live.
- Finish after saving the completed JSON file.
