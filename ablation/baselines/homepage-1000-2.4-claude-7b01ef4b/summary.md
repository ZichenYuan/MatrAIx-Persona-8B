# homepage: 1000 of 1000 trials finished — pg-web-infobric-audit-v2-homepage-7b01ef4b

## 1. Coverage (pipeline health — gate, not a result)

- Launched 1000, finished 1000, passed verifier 999 (99.9%), failed 1
  - 1 × verifier scored 0 (no exception)
- Artifact parse: clean 999 (clean rate 100.0%)
- Instrument ['2.4', '2.5'], variant ['full'], device {'desktop': 999}
- Values the verifier could not map onto the answer set: 3 across 3 trials

## 2. Who was simulated (finished trials)

- **traffic_segment**: Prospect (evaluating a supplier) 499 (49.9%); Existing customer (login or support) 340 (34.0%); Job seeker 55 (5.5%); Mis-click from a search result or an ad 45 (4.5%); Supplier or partner (selling to Infobric) 30 (3.0%); Student or researcher 30 (3.0%)
- **audience_group**: Finance or administration 238 (23.8%); Supervisor or daily user 204 (20.4%); Not a target visitor 160 (16.0%); Fleet, equipment or rental manager 132 (13.2%); Operations, project or site manager 114 (11.4%); Owner or senior manager 109 (10.9%); HSE or compliance 42 (4.2%)
- **tier**: Rental 202 (20.2%); Main contractor 181 (18.1%); Subcontractor 173 (17.3%); Vehicle and field service business 168 (16.8%); Not applicable 160 (16.0%); Developer 115 (11.5%)
- **visit_intent**: Existing customer: came to log in or reach support, not to evaluate 340 (34.0%); Has a specific problem to solve right now 251 (25.1%); Exploring ways to improve operations 248 (24.8%); Looking for job openings at Infobric 55 (5.5%); Landed here by mistake from a search result or an ad 45 (4.5%); Wants to sell services or products to Infobric 30 (3.0%); Researching the company for a school or university assignment 30 (3.0%)
- **infobric_familiarity**: Has never heard of Infobric 361 (36.1%); Uses Infobric at work today 340 (34.0%); Has heard the name but knows nothing more 227 (22.7%); Has seen Infobric equipment or the logo on a site 71 (7.1%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 488 of 999 = **48.8%**
- Would keep reading (`would_continue`): yes 511, no 488
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Finance or administration | 238 | 40.3% | 59.7% |
| Supervisor or daily user | 204 | 41.7% | 58.3% |
| Not a target visitor | 160 | 88.1% | 11.9% |
| Fleet, equipment or rental manager | 132 | 40.2% | 59.8% |
| Operations, project or site manager | 114 | 38.6% | 61.4% |
| Owner or senior manager | 109 | 54.1% | 45.9% |
| HSE or compliance | 42 | 23.8% | 76.2% |

| Traffic segment | n | left early | would continue = yes | next step: leave | go to login |
|---|---:|---:|---:|---:|---:|
| Prospect (evaluating a supplier) | 499 | 1.4% | 98.6% | 1.4% | 0.0% |
| Existing customer (login or support) | 340 | 100.0% | 0.0% | 0.0% | 88.2% |
| Job seeker | 55 | 100.0% | 0.0% | 0.0% | 0.0% |
| Mis-click from a search result or an ad | 45 | 100.0% | 0.0% | 100.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 30 | 100.0% | 0.0% | 0.0% | 0.0% |
| Student or researcher | 30 | 36.7% | 63.3% | 23.3% | 0.0% |

## 3b. Trust as a ladder of commitments (yes/no, rising cost) plus one belief item

- **Would give a work email for a guide**: yes 37.7% of 999
- **Would ask for a call-back**: yes 5.0% of 999
- **Would book a demo this week**: yes 0.0% of 999
- **Would run a pilot on own data this month**: yes 0.0% of 999
- **Would accept the proof claim unchecked**: yes 69.8% of 999
- **Rungs accepted (0-4)**: mean 0.43, sd 0.59, distribution 0: 622, 1: 327, 2: 50, 3: 0, 4: 0; inconsistent ladders (a yes above a no) 0 of 999
- η² by visitor kind 0.12 · by traffic segment 0.53 · by visit intent 0.61

| Group | n | mean rungs | give a work email for a guide | ask for a call-back | book a demo this week | run a pilot on own data this month | accept the proof claim unchecked |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prospect (evaluating a supplier) | 499 | 0.86 | 75.6% | 10.0% | 0.0% | 0.0% | 48.9% |
| Existing customer (login or support) | 340 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Job seeker | 55 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 89.1% |
| Mis-click from a search result or an ad | 45 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 73.3% |
| Supplier or partner (selling to Infobric) | 30 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 70.0% |
| Student or researcher | 30 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 33.3% |
| Finance or administration | 238 | 0.47 | 45.0% | 1.7% | 0.0% | 0.0% | 68.9% |
| Supervisor or daily user | 204 | 0.44 | 40.2% | 3.4% | 0.0% | 0.0% | 71.1% |
| Not a target visitor | 160 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 70.6% |
| Fleet, equipment or rental manager | 132 | 0.52 | 43.9% | 7.6% | 0.0% | 0.0% | 63.6% |
| Operations, project or site manager | 114 | 0.65 | 52.6% | 12.3% | 0.0% | 0.0% | 77.2% |
| Owner or senior manager | 109 | 0.51 | 40.4% | 11.0% | 0.0% | 0.0% | 72.5% |
| HSE or compliance | 42 | 0.69 | 61.9% | 7.1% | 0.0% | 0.0% | 57.1% |
| Existing customer: came to log in or reach support, not to evaluate | 340 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Has a specific problem to solve right now | 251 | 1.09 | 88.8% | 19.9% | 0.0% | 0.0% | 49.4% |
| Exploring ways to improve operations | 248 | 0.62 | 62.1% | 0.0% | 0.0% | 0.0% | 48.4% |
| Looking for job openings at Infobric | 55 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 89.1% |
| Landed here by mistake from a search result or an ad | 45 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 73.3% |
| Wants to sell services or products to Infobric | 30 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 70.0% |
| Researching the company for a school or university assignment | 30 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 33.3% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 998 | 4.06 | 0.41 | 0.0% | 0.0% | 5.3% | 83.1% | 11.6% |  |
| language_relevance | 511 | 3.58 | 0.58 | 0.0% | 4.1% | 34.6% | 60.7% | 0.6% |  |
| practical_value | 511 | 3.01 | 0.39 | 0.4% | 5.9% | 86.3% | 7.4% | 0.0% |  |
| trust | 511 | 3.00 | 0.15 | 0.0% | 1.0% | 97.8% | 1.2% | 0.0% | **collapsed** (sd < 0.3) |
| next_step_confidence | 511 | 3.25 | 0.44 | 0.0% | 0.2% | 74.6% | 25.2% | 0.0% |  |
| next_step_ease | 511 | 3.90 | 0.32 | 0.2% | 0.0% | 9.6% | 90.0% | 0.2% |  |
| cta_match | 511 | 3.98 | 0.30 | 0.2% | 0.0% | 4.3% | 92.6% | 2.9% | **collapsed** (sd < 0.3) |
| contact_likelihood | 511 | 2.35 | 0.69 | 4.3% | 64.2% | 23.5% | 8.0% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Finance or administration | 238 | 4.03 | 3.41 | 2.99 | 2.99 | 3.15 | 3.88 | 3.96 | 2.27 |
| Supervisor or daily user | 204 | 4.09 | 3.78 | 3.08 | 2.97 | 3.18 | 3.86 | 3.95 | 2.28 |
| Not a target visitor | 160 | 3.84 | 2.00 | 1.89 | 3.21 | 3.89 | 4.05 | 4.58 | 1.00 |
| Fleet, equipment or rental manager | 132 | 4.11 | 3.46 | 2.99 | 2.99 | 3.18 | 3.91 | 3.95 | 2.47 |
| Operations, project or site manager | 114 | 4.16 | 3.89 | 3.10 | 3.01 | 3.43 | 3.91 | 3.96 | 2.64 |
| Owner or senior manager | 109 | 4.22 | 3.74 | 3.18 | 3.00 | 3.34 | 3.94 | 3.96 | 2.66 |
| HSE or compliance | 42 | 4.14 | 3.88 | 3.03 | 3.03 | 3.25 | 3.94 | 3.97 | 2.38 |

## 4b. In-browse vs scored after the visit (Finding 1 replication)

496 of 999 trials re-scored outside the browser by claude-opus-4.8, from the persona text plus the persona's own notes (application/scripts/score_audit.py). Where scoring was scoped to prospects, this section is about prospects. η² = share of score variance explained by the persona dimension; 0.01 small, 0.06 medium, 0.14 large.

| Score | mean in-browse | sd | mean scored | sd | η² visitor kind (in / scored) | η² tier (in / scored) | η² visit intent (in / scored) | values used (scored) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 3.98 | 0.21 | 4.17 | 0.40 | 0.02 / 0.04 | 0.05 / 0.13 | 0.00 / 0.00 | [3, 4, 5] |
| language_relevance | 3.64 | 0.50 | 3.98 | 0.64 | 0.16 / 0.13 | 0.28 / 0.30 | 0.01 / 0.00 | [2, 3, 4, 5] |
| practical_value | 3.05 | 0.32 | 2.98 | 0.41 | 0.04 / 0.05 | 0.07 / 0.10 | 0.00 / 0.00 | [2, 3, 4] |
| trust | 2.99 | 0.12 | 3.08 | 0.30 | 0.02 / 0.04 | 0.01 / 0.02 | 0.00 / 0.00 | [2, 3, 4] |
| next_step_confidence | 3.22 | 0.42 | 3.51 | 0.52 | 0.06 / 0.01 | 0.02 / 0.01 | 0.03 / 0.00 | [2, 3, 4] |
| next_step_ease | 3.89 | 0.33 | 3.50 | 0.52 | 0.01 / 0.01 | 0.02 / 0.01 | 0.00 / 0.01 | [1, 2, 3, 4] |
| cta_match | 3.96 | 0.26 | 3.93 | 0.55 | 0.00 / 0.02 | 0.02 / 0.01 | 0.00 / 0.01 | [1, 2, 3, 4, 5] |
| contact_likelihood | 2.40 | 0.65 | 2.64 | 0.75 | 0.06 / 0.03 | 0.02 / 0.04 | 0.41 / 0.49 | [1, 2, 3, 4] |

### Scored after the visit, by visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Finance or administration | 144 | 4.15 | 3.74 | 2.97 | 3.04 | 3.48 | 3.46 | 3.91 | 2.54 |
| Supervisor or daily user | 119 | 4.19 | 4.19 | 3.08 | 3.05 | 3.58 | 3.53 | 4.03 | 2.50 |
| Fleet, equipment or rental manager | 79 | 4.00 | 3.68 | 2.86 | 3.04 | 3.46 | 3.42 | 3.79 | 2.72 |
| Operations, project or site manager | 70 | 4.21 | 4.23 | 2.97 | 3.19 | 3.47 | 3.59 | 3.97 | 2.81 |
| Owner or senior manager | 52 | 4.31 | 4.12 | 3.08 | 3.10 | 3.52 | 3.50 | 3.90 | 2.81 |
| HSE or compliance | 32 | 4.19 | 4.16 | 2.78 | 3.19 | 3.62 | 3.56 | 3.88 | 2.66 |

## 5. What they would do next

- **Next step**: learn_more 343 (34.3%); go_to_login 300 (30.0%); go_elsewhere_on_site 222 (22.2%); leave 59 (5.9%); contact_sales 48 (4.8%); come_back_later 27 (2.7%)
- **Needed before going further**: would_not_proceed 518 (51.9%); need_references_first 478 (47.8%); unknown 3 (0.3%)
- **Main basis of the decision**: other 362 (36.2%); fit 356 (35.6%); features 104 (10.4%); support 97 (9.7%); price 49 (4.9%); integrations 14 (1.4%); proof_references 11 (1.1%); consolidation 6 (0.6%)
- Converted (contact / demo / trial as the next step): 48 of 999 = 4.8%
- Information they missed most: price 492; references 430; setup_time 334; integrations 271; data_privacy 177; hardware 159
- Weakest part of the page: top 396, unknown 320, middle 254, bottom 29 · strongest: top 421, middle 367, unknown 207, bottom 4

| Visitor kind | learn_more | go_to_login | go_elsewhere_on_site | leave | contact_sales | come_back_later |
|---|---:|---:|---:|---:|---:|---:|
| Finance or administration | 44.5% | 35.7% | 12.2% | 1.3% | 2.1% | 4.2% |
| Supervisor or daily user | 41.7% | 35.8% | 16.2% | 0.5% | 3.4% | 2.5% |
| Not a target visitor | 0.0% | 0.0% | 67.5% | 32.5% | 0.0% | 0.0% |
| Fleet, equipment or rental manager | 40.9% | 34.1% | 15.2% | 0.8% | 6.1% | 3.0% |
| Operations, project or site manager | 40.4% | 34.2% | 13.2% | 0.0% | 11.4% | 0.9% |
| Owner or senior manager | 25.7% | 45.0% | 12.8% | 1.8% | 11.0% | 3.7% |
| HSE or compliance | 57.1% | 21.4% | 7.1% | 0.0% | 7.1% | 7.1% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 999
- Grounding: quoted claims found on the page 0.985, quoted phrases found on the page 0.958; trials with any ungrounded quote 164 of 999
- Primary button: inspected 51.2%, landed on the expected page 100.0%, label quoted correctly 100.0%
