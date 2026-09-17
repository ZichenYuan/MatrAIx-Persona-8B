# Review one page of a supplier's website

Read the scenario in `input/context.md` — find the one that matches **your Tier** —
then open the page below and review it with that situation in mind. Use only what
is visible on the page. Do not log in, submit any form, book a demo, or contact
anyone.

Page to review: **https://infobric.com/se/**

The page is in Swedish. Read it in Swedish; write your answers in English.

Save your review to `/app/output/page_audit.json`:

```json
{
  "page_url": "https://infobric.com/se/",
  "page_id": "homepage",
  "page_label": "Infobric homepage",
  "one_sentence_summary": "<in one sentence, what does this page say the company offers?>",
  "fact_customers_claimed": "<the number of customers or users the page claims, exactly as shown, or 'not found'>",
  "clarity": <1-7>,
  "relevance": <1-7, relevance to your own situation and role>,
  "trust": <1-7>,
  "trust_signals_noticed": ["<zero or more of: logos, customer_count, testimonial, case_studies, certifications>"],
  "missing_info": ["<zero or more of: price, integrations, hardware, setup_time, references, data_privacy, contract_terms>"],
  "next_step": "<one of: contact_sales, book_demo, try_free, learn_more, come_back_later, leave>",
  "basis_primary": "<the main thing that drove your next step — one of: price, quality, features, convenience, taste, trust, familiarity, novelty, fit, other>",
  "tone_and_visuals": "<one line on tone and visuals>",
  "reason": "<why you chose that next step, grounded in this page and your situation>"
}
```

Requirements:

- `clarity`, `relevance`, `trust` are whole numbers from 1 (worst) to 7 (best).
- `trust_signals_noticed` and `missing_info` may be empty lists, but must only
  use the listed values.
- `fact_customers_claimed` must be copied from the page if present; do not guess.
- `next_step` must reflect what you would genuinely do next given your situation.
  Be realistic about what each option costs you: `contact_sales` and `book_demo`
  mean handing over your details and committing your own time to a sales
  conversation and the follow-up calls that come after it — most people do not do
  that from one page. `learn_more` (keep reading this site), `come_back_later`
  and `leave` are equally valid answers, and `leave` is right if the page does not
  give you what you need. Choose the step you would actually take today.
- `basis_primary` is the single biggest factor behind that choice.
- Keep `reason` specific to this page and to your own situation.
- Finish after saving the completed JSON file.
