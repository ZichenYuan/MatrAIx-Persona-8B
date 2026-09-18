# Visit a supplier's website

You are looking into **Infobric** for the situation described in your context. Start
on their homepage and browse the site the way you actually would — follow whatever
looks relevant to you, skip what does not, and stop when you have seen enough or
have run out of patience.

Start here: https://infobric.com/se/

You have a browsing budget of **about 25 actions** (a click, a navigation, a scroll,
or a back step each count as one). The budget is for browsing only. Saving the
questionnaire is always required and never counts against it — there is no clock,
and the task does not end until you have saved the file. When you have seen enough,
or are close to the budget, stop browsing, decide what you would actually do next,
and fill in the short questionnaire below.

Use only what is visible on the site. You may open a contact, demo or trial page to
see what it asks for, but do not log in, submit any form, book anything, or contact
anyone.

The site is in Swedish. Read it in Swedish; write your answers in English.

Save your answers to `/app/output/free_visit.json`:

```json
{
  "start_url": "https://infobric.com/se/",
  "pages_visited": ["<every distinct page you opened, in the order you opened them, as full URLs — the first one is the start URL>"],
  "exit_page": "<the full URL of the page you were on when you stopped>",
  "reached_pricing": <true or false — did you open a page that shows prices or packages>,
  "reached_contact": <true or false — did you open a contact, demo-booking or free-trial page>,
  "steps_used": <roughly how many actions you took>,
  "stopped_because": "<one of: found_enough, ran_out_of_steps, could_not_find, lost_interest>",
  "found_what_needed": "<one of: yes, partly, no>",
  "biggest_obstacle": "<the one thing that most got in your way on this site, named concretely, or 'none'>",
  "conclusion": "<in one sentence, what you now believe this supplier offers for someone in your situation>",
  "clarity": <1-7, after your visit, how clear it is what this would actually do for you and your sites>,
  "trust": <1-7, how far you would trust this supplier with your own site data and a multi-year contract>,
  "contact_likelihood": <1-7, how likely you are to contact this supplier within the next week>,
  "trust_action": "<what you would need before going any further — one of: share_data_now, need_references_first, need_pilot_first, would_not_proceed>",
  "missing_info": ["<zero or more of: price, integrations, hardware, setup_time, references, data_privacy, contract_terms>"],
  "next_step": "<one of: contact_sales, book_demo, try_free, learn_more, come_back_later, leave>",
  "basis_primary": "<the main thing driving that step — one of: legal_compliance, consolidation, price, integrations, ease_of_rollout, proof_references, support, features, fit, other>",
  "improvement_suggestion": "<the single change to this site that would most move you toward contacting them, in your own words>",
  "reason": "<why you chose that next step, grounded in what you saw and your own situation>"
}
```

Requirements:

- **Never end without saving the file.** If you have fewer than three actions left,
  stop browsing and save your answers with what you have. An honest short visit is a
  valid result; an unsaved one is not. Nothing ends this run except your own final
  action — if you ever think the run has already ended, it has not: save the file.
- `pages_visited` must be honest and complete: every distinct page you opened, in
  order, as the full URL shown in the address bar. Do not list pages you only saw
  links to. `exit_page` must be the last entry.
- `clarity`, `trust`, `contact_likelihood` are whole numbers from 1 (worst / least
  likely) to 7 (best / most likely). Use the whole range — 4 means genuinely
  undecided, not a polite default.
- `contact_likelihood` is about your own next week, not how good the site is.
  Contacting them costs you a sales conversation and follow-up calls; weigh that
  against how pressing your situation actually is. Someone facing a deadline with no
  system in place may well reach out; someone with time and a working setup may not.
  Let your own situation decide.
- Anchor the ratings to real behaviour, not politeness. For `clarity`, 7 means you
  could explain to a colleague what you would buy and why; 1 means you still do not
  know what they sell. For `trust`, 7 means you would put your own sites on it
  without asking for references; 1 means you would not share your data with them.
  If the visit genuinely left you unsure, say so with a low number — 5 for everything
  is not a real answer.
- `trust_action` is the concrete thing you would need before going further, given
  what you saw. `share_data_now` means you would sign up or hand over site details
  today.
- `missing_info` may be an empty list, but must use only the listed values, spelled
  exactly as shown.
- `next_step` must be what you would actually do today. `learn_more`,
  `come_back_later` and `leave` are all valid, and `leave` is right if the site does
  not give you what you need.
- `basis_primary` is the single thing that actually drives your next step. Use `fit`
  only when no more specific reason applies.
- `biggest_obstacle` and `improvement_suggestion` must name something concrete you
  ran into or wanted — "the pricing page hides the per-user price", "no page for
  rental companies" — not a general impression.
- Keep `reason` specific to what you saw and your own situation.
- **Save the file with your file-writing tool** (for example `write_file`) to exactly
  `/app/output/free_visit.json`, then read it back and check it is complete, valid
  JSON. Do not try to run Python or shell commands to write it — you may not have
  them, and you do not need them. Write your answers in English; if you quote a
  Swedish phrase, write it as-is inside the JSON string.
- If your file tool adjusts or auto-corrects the save path (for example into a
  sandbox subdirectory), that is expected and acceptable — the saved file is still
  correct. Do **not** treat a path adjustment as a failure, and do not report the
  task as unsuccessful because of it.
- If a page looks blank or empty after you navigate, that is almost always a slow
  render, not a broken site. Wait a moment and reload it, and try once more before
  concluding anything. Do not end the task by reporting an empty page — the site is
  known to be live.
- Finish after saving the completed JSON file.
