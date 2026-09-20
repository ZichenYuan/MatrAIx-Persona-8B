# The button: what we measure at the call to action, and why

*Reference note, 2026-09-20. Numbers are from the 1,000-persona homepage run
(`pg-web-infobric-audit-v2-homepage-7b01ef4b`, Claude Opus 4.8, instrument 2.4/2.5) unless
another page is named. The four product-page studies use the same instrument.*

## 1. Why the button at all

The page is where a visitor forms an opinion; the button is where the opinion turns into an
act, or fails to. Four reasons it carries more weight than its size on the page suggests.

**The partner asked for it, explicitly and per page.** The Main Brief §6 says "For product
pages, follow the primary CTA and compare the expectation it creates with what actually
follows", and every URL brief writes out what its buttons should lead a visitor to expect:
a free trial should mean "get started with limited commitment", a demo should mean "a needs
analysis and a relevant walkthrough", the Fleet preview should mean "see their vehicles and
current status". Those are testable sentences, and the only way to test them is to click.

**It is the one place where a gap is measurable rather than inferable.** Analytics can show
that a button was clicked and that a form was not submitted. It cannot say what the visitor
thought would happen. We capture the expectation *before* the click and the reality *after*,
so the difference between them is a number and a quote, not an inference.

**It is where trust becomes behaviour.** The trust ladder asks what a visitor would commit
to; the button is the same question asked by the page itself. When 76% would give a work
email but only 10% would take a call-back, the design question is whether the page's one
button is asking for the cheap thing or the expensive one.

**It doubles as proof the simulation actually happened.** A persona that never opened the
page can still produce plausible prose. It cannot produce the right button label and the
right destination. Label grounding and destination checks are the cheapest validity gate we
have, and they run on every trial.

## 2. What is recorded at the button

Ten fields, in the order the visitor meets them.

| Field | What it holds | Kind |
|---|---|---|
| `next_step` | which route the visitor would actually take, from the page's own option set | choice |
| `primary_cta_seen` | the button's label, quoted exactly as written on the page | text, grounded |
| `cta_expectation` | what they expected before clicking | text |
| `cta_inspected` | whether they clicked it at all | yes/no |
| `cta_page_url` | where they landed | url, grounded |
| `cta_reality` | what actually appeared and what it asks of them | text |
| `form_asks_for` | each thing a form demands; empty when there is no form | list |
| `cta_match` | how well reality met the expectation, 1–5 | rating |
| `next_step_confidence` | whether they know what happens after clicking, 1–5 | rating |
| `next_step_ease` | whether the step is quick or off-putting, 1–5 | rating |

The verifier adds three checks the visitor does not control: `cta_label_grounded` (is that
label really on the page), `cta_url_ok` (is that destination one the page offers), and, on
the pages that show them, `price_found` and `package_fit` for what the visitor learned on
the way.

Two rules keep the measurement honest. **One click, nothing submitted**: no form is filled,
nothing is booked, no account is created, so we never pollute the partner's analytics or
their sales pipeline. And **anything uninspected is `unknown`, never a guess** — a visitor
who left after the first screen has no CTA answers at all, which is why `cta_inspected` runs
at 51% on the homepage: it is 100% of the people who read the page.

## 3. The variations, and why each page differs

| Page | What the visitor is asked to do | Why |
|---|---|---|
| Homepage | click the one contact or demo route | the page offers a single commercial next step |
| Fleet | **choose** among free trial, demo, order a package, preview your fleet, then click that one | the partner wrote a separate expectation for each; pinning everyone to one button tests one of four |
| Driving log | choose among free trial and guide download | same reason; `book_demo` was removed after we found no such button on the live page |
| Equipment | choose among free account, demo, calculator | same reason |
| Hyrma | click "Få en demo" | the page genuinely has one route |

The choice variant is the one design decision worth defending. It costs comparability —
`cta_match` becomes an average over different buttons — and buys the partner's actual
question, which is *which* way of getting started suits which visitor. The report handles the
cost by grouping the expectation-versus-reality narrative by the button the visitor named.

Three further variations exist in the instrument and are not yet run: the **skim** variant
(first screen only, no CTA at all), the **stimulus-contrast** arm (the same page with the
proof line removed), and model arms. Only the last has been exercised, on GPT-5.6 Luna
versus Claude Opus 4.8.

## 4. What the homepage run found at the button

Of 999 visits, 511 people read the page and every one of them clicked. Every label they
quoted was real («Kontakt» 420, «Kontakta oss» 91) and 505 of 511 reached the contact page;
six clicked a "Kontakt" element that returned them to the homepage, which is a small
navigation defect worth passing on.

Expectation match was 3.98 out of 5 with almost no spread, and ease of the next step 3.90.
Read together with what they wrote, that is not praise: the button does what it says, and the
disappointment is elsewhere.

**The finding that matters is what is behind the button.** The contact route does not lead to
a form. It lands on a page offering a phone number, a chat link, a list of offices and a
second button, «Lämna ett meddelande», with the form behind that. 510 of the 511 described
exactly this, which is why `form_asks_for` is empty almost everywhere — correctly so, there
was no form on the page they reached. So a visitor who has decided to make contact meets one
more decision and one more click. That is the cost sitting between intent and conversion,
and it is invisible in click analytics.

It also explains a number that would otherwise look odd: only 48 of 499 prospects chose
"contact sales" as their next step, while 343 chose "learn more" and 74 would go to another
page of the site. The button is not the obstacle; the missing price, references and
integration facts are, and the extra step does not help.

## 5. Known limits

- `cta_match` has almost no spread on the homepage (sd 0.30). It may come alive on the
  product pages, where the button is a signup rather than a contact route, and Equipment's
  hero button scrolls to a price table instead of a form. If it stays flat there, the rating
  is decoration and the free-text expectation and reality fields carry the section alone.
- Form starts, submissions, confirmation messages and the first follow-up are all named in
  the partner's brief and are all out of scope by design, because we never submit. The
  report says so rather than leaving it silent.
- The destination check was vacuous on the product pages until the buttons were opened by
  hand on 2026-09-19: every inventory listed its own page path, so any click that stayed on
  the page passed. Real destinations are now recorded, including the one that leaves
  infobric.com for an external app.
