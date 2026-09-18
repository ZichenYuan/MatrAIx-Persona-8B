# Review one page of a supplier's website

Review the page named below, as yourself and in your own situation.

## Page brief

- **page_id:** `homepage`
- **Page to review:** https://infobric.com/se/

This is the supplier's front page — the first thing most visitors see.

Use only what is visible on the page. Do not log in, submit any form, book a demo,
or contact anyone.

The site is in Swedish. Read it in Swedish; write your answers in English.

Save your review to `/app/output/page_audit.json`:

```json
{
  "page_id": "<the page_id given in the Page brief>",
  "page_url": "<the exact URL you actually reviewed>",
  "one_sentence_summary": "<in one sentence, what does this page say or offer?>",
  "key_claim_noticed": "<the most specific factual claim on this page, quoted as shown, or 'none'>",
  "clarity": <1-7, how clear it is what this would actually do for you and your sites — not how tidy the page looks>,
  "relevance": <1-7, relevance to your own situation and role>,
  "trust": <1-7, how far you would trust this supplier with your own site data and a multi-year contract>,
  "contact_likelihood": <1-7, how likely you are to contact this supplier within the next week>,
  "trust_signals_noticed": ["<zero or more of: logos, customer_count, testimonial, case_studies, certifications>"],
  "missing_info": ["<zero or more of: price, integrations, hardware, setup_time, references, data_privacy, contract_terms>"],
  "next_step": "<one of: contact_sales, book_demo, try_free, learn_more, come_back_later, leave>",
  "basis_primary": "<the main thing driving that step — one of: legal_compliance, consolidation, price, integrations, ease_of_rollout, proof_references, support, features, fit, other>",
  "strongest_element": "<the one thing on this page that worked best for you — name the actual element>",
  "weakest_element": "<the one thing on this page that worked worst for you — name the actual element>",
  "improvement_suggestion": "<the single change to this page that would most move you toward contacting them, in your own words>",
  "tone_and_visuals": "<one line on tone and visuals>",
  "reason": "<why you chose that next step, grounded in this page and your situation>"
}
```

Requirements:

- `clarity`, `relevance`, `trust`, `contact_likelihood` are whole numbers from 1
  (worst / least likely) to 7 (best / most likely). Use the whole range — 4 means
  genuinely undecided, not a polite default.
- `contact_likelihood` is about your own next week, not how good the page is. Contacting
  them costs you a sales conversation and follow-up calls; weigh that against how pressing
  your situation actually is. Someone facing a deadline with no system in place may well
  reach out; someone with time and a working setup may not. Let your own situation decide.
- `trust_signals_noticed` and `missing_info` may be empty lists, but must use only
  the listed values, spelled exactly as shown.
- `next_step` must be what you would actually do today. `learn_more`,
  `come_back_later` and `leave` are all valid, and `leave` is right if the page
  does not give you what you need.
- `strongest_element` and `weakest_element` must name something concrete you saw —
  "the customer logos", "the list of 14 products", "the headline" — not a general
  impression.
- `improvement_suggestion` is advice to the page's owner. Be specific and say what
  it would unlock for you.
- Keep `reason` specific to this page and your own situation.
- Anchor the 1-7 ratings to real behaviour, not politeness. For `clarity`, 7 means
  you could explain to a colleague what you would buy and why; 1 means you still do
  not know what they sell. For `trust`, 7 means you would put your own sites on it
  without asking for references; 1 means you would not share your data with them.
  If a page genuinely leaves you unsure, say so with a low number — 5 for everything
  is not a real answer.
- `basis_primary` is the single thing that actually drives your next step. Use `fit`
  only when no more specific reason applies.
- **Save the file with your file-writing tool** (for example `write_file`) to exactly
  `/app/output/page_audit.json`, then read it back and check it is complete, valid
  JSON. Do not try to run Python or shell commands to write it — you may not have
  them, and you do not need them. Write your answers in English; if you quote a
  Swedish phrase, write it as-is inside the JSON string.
- **Never end without saving the file.** Nothing ends this run except your own final
  action — if you ever think the run has already ended, it has not: save the file.
- If your file tool adjusts or auto-corrects the save path (for example into a
  sandbox subdirectory), that is expected and acceptable — the saved file is still
  correct. Do **not** treat a path adjustment as a failure, and do not report the
  task as unsuccessful because of it.

- If the page looks blank or empty after you navigate, that is almost always a slow
  render, not a broken site. Wait a moment and reload it, and try once more before
  concluding anything. Do not end the task by reporting an empty page — the pages in
  this study are known to be live.
- Finish after saving the completed JSON file.
