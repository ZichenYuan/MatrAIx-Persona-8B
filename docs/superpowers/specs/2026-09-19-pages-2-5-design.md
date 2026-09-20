# Pages 2–5 on instrument 2.4: Fleet, Electronic Driving Log, Equipment, Hyrma

*Design note, 2026-09-19, written while the homepage full run (`7b01ef4b`) is going.
Follows `2026-09-19-instrument-2-4-design.md`. Nothing here is applied to
`application/tasks/` until that job finishes: regenerating a task dir mid-run changes
Harbor's job lock and makes retry impossible.*

## 1. What the four pages are, from the partner's own briefs and their analytics

| | Fleet | Driving log | Equipment | Hyrma |
|---|---|---|---|---|
| GA4 sessions (90 d) | 3,970 | 1,818 | 430 | 24,767 |
| Quick Backs | 41% | **28%** (lowest) | 33% | 26% |
| Scroll depth | 29% | **46%** (deepest) | 42% | 24% |
| Pages per session | — | 2.72 | **4.18** (most exploratory) | 1.49 |
| Login events / Clarity sessions | — | 13% | 21% | **38%** |
| Returning users | — | **19%** (mostly new) | 34% | **61%** |
| Conversion rate | **2.19%** (highest) | 1.32% | 1.86% | **0.02%** |
| Primary CTA | Prova gratis | Prova gratis | Prova gratis | Få en demo |
| Price on the page | yes | yes | yes | yes |

Three page characters fall out of this, and they need different simulated populations:

- **Driving log is a near-pure evaluation page.** Four fifths of its visitors are new,
  almost nobody logs in, it is read deepest and bounced least. It is also the page whose
  search term ("elektronisk körjournal") a private person might plausibly land on by
  mistake.
- **Hyrma is a login door wearing a product page.** Six in ten visitors are returning,
  more than a third fire a login event, and it converts four times in ninety days. The
  question for this page is not "does the sales pitch work" but "is the sales pitch
  reaching anyone at all, or is this page doing a different job?"
- **Fleet and Equipment are ordinary product pages**, Equipment being the most
  exploratory (4.18 pages per session) and carrying the site's highest dead-click (5.7%)
  and JS-error (3.9%) rates.

## 2. The finding these pages can deliver that the homepage could not

Every homepage prospect said price, integrations and setup time were missing: 19 of 20
in the smoke, and the same at scale. **All four product pages show prices.** So the
question becomes a measurable one: when the information visitors say they need is on the
page, do they find it, and does it move them up the trust ladder? That is a genuinely
new answer for the partner, and it is only available because the same instrument runs on
both kinds of page.

Second cross-page finding: each page leads with a different *kind* of proof claim, so one
run gives a comparison of which claim types are believed.

| Page | Proof claim | Claim type |
|---|---|---|
| Homepage | «Betrodd av över 12 000 kunder och 450 000 användare» | customer count |
| Fleet | «Över 20 år i branschen.» | tenure |
| Driving log | «Här är varför över 7500 företag väljer oss:» | customer count |
| Equipment | «3 års batteritid.» | product specification |
| Hyrma | «Sveriges främsta uthyrningssystem» | superlative (changed from a customer testimonial, which is not a vendor claim) |

## 3. Population per page

Prospects and existing customers keep the page's relevance filter (`deals_with_vehicles`,
`deals_with_driving_logs`, `deals_with_tools_equipment`, `works_in_rental_process`), as
the partner asks: do not let someone with no vehicles review the Fleet page. Wrong-fit
personas carry "Not part of my job" on every one of those fields, so a filtered pool
excludes them automatically. That is correct for Fleet, Equipment and Hyrma: a job seeker
does not land on `/produkter/hyrma/`. It is wrong for the driving log, where a private
person searching for a driving-log app genuinely does.

So each page gets its own pool, built by `build_traffic_mix_pool.py --filter`, which
applies the relevance filter to the prospect and customer halves only and leaves the
wrong-fit mini-pool alone.

| Page | prospects | existing customers | wrong-fit | why |
|---|---:|---:|---:|---|
| Fleet | 70% | 25% | 5% | product landing, some customer traffic assumed from the homepage's login share |
| Driving log | 75% | 10% | 15% | 81% new users, 13% login; the mis-click case is real here |
| Equipment | 70% | 25% | 5% | 34% returning, 21% login |
| Hyrma | 45% | 50% | 5% | 61% returning, 38% login: the login-door hypothesis is the point of this page |

Sample size: 200 per page (about 140 prospects on the three product pages, ~28 per
relevant visitor kind; Hyrma 90 prospects). Four pages ≈ 800 trials ≈ 7 hours at
concurrency 4, and they can run one after another rather than in one sitting.

## 4. Instrument changes, all small

1. **`go_to_login` and `go_elsewhere_on_site` on every page.** All four pages carry
   "Logga in"; without the first, a customer who came to log in has no honest next step,
   and the bounce/route split that made the homepage numbers readable breaks down.
2. **Hyrma's proof claim** becomes «Sveriges främsta uthyrningssystem». The current one
   is a customer's own words, so "would you accept it without checking" does not read as
   a claim about the supplier.
3. **Equipment brief gains one line**: if something looks clickable and does nothing, or
   the page misbehaves, record it in `confusing_or_missing`. The partner's Clarity data
   flags 5.7% dead clicks and 3.9% JS errors on this page; personas can say what those
   clicks were aimed at, which Clarity cannot.
4. Nothing else changes. The six dimensions, the trust ladder, the exit form and the
   per-page `next_step` sets already carry the partner's per-URL questions.

## 5. What each page's report answers, mapped to the partner's briefs

- **Fleet** (§ "which way of getting started is right for them"): the `next_step`
  distribution across trial / demo / package / fleet preview, per visitor kind, with the
  expectation-versus-reality gap for the one CTA each persona actually clicks.
- **Driving log** (§ installation, integrations, privacy and security): what a first-time
  reader still cannot answer after the deepest-read page on the site, and whether the
  stated price and ISO/GDPR wording is believed.
- **Equipment** (§ check-in/check-out, service, calibration): whether the mechanics are
  understood, plus the dead-click list.
- **Hyrma** (§ bookings, contracts, pricing, multiple depots): the routed-versus-stayed
  split first, then, for the prospects who do read, whether a rental business can tell
  the packages apart and what the 27,500 kr start-up cost does to the trust ladder.

## 6. Order of work, after the homepage run finishes

1. `build_traffic_mix_pool.py --filter` for each page (four pools).
2. Template edits (already made: briefs, inventories, Hyrma claim, Equipment line).
3. `make_audit_v2_tasks.py` — regenerates all five task dirs, which is why it waits.
4. Oracle check per page (`solution/solve.sh`), then a 20-persona probe per page before
   the 200-persona runs.
