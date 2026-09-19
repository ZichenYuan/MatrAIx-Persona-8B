# homepage: 50 of 50 trials finished — pg-web-infobric-audit-v2-homepage-58a824d2

## 1. Coverage (pipeline health — gate, not a result)

- Launched 50, finished 50, passed verifier 50 (100.0%), failed 0
- Artifact parse: clean 50 (clean rate 100.0%)
- Instrument ['2.4'], variant ['full'], device {'desktop': 50}
- Values the verifier could not map onto the answer set: 0 across 0 trials

## 2. Who was simulated (finished trials)

- **traffic_segment**: Existing customer (login or support) 23 (46.0%); Prospect (evaluating a supplier) 20 (40.0%); Job seeker 3 (6.0%); Mis-click from a search result or an ad 2 (4.0%); Supplier or partner (selling to Infobric) 1 (2.0%); Student or researcher 1 (2.0%)
- **audience_group**: Finance or administration 14 (28.0%); Fleet, equipment or rental manager 10 (20.0%); Not a target visitor 7 (14.0%); Owner or senior manager 7 (14.0%); Supervisor or daily user 6 (12.0%); Operations, project or site manager 5 (10.0%); HSE or compliance 1 (2.0%)
- **tier**: Main contractor 11 (22.0%); Rental 10 (20.0%); Subcontractor 10 (20.0%); Vehicle and field service business 9 (18.0%); Not applicable 7 (14.0%); Developer 3 (6.0%)
- **visit_intent**: Existing customer: came to log in or reach support, not to evaluate 23 (46.0%); Has a specific problem to solve right now 13 (26.0%); Exploring ways to improve operations 7 (14.0%); Looking for job openings at Infobric 3 (6.0%); Landed here by mistake from a search result or an ad 2 (4.0%); Wants to sell services or products to Infobric 1 (2.0%); Researching the company for a school or university assignment 1 (2.0%)
- **infobric_familiarity**: Uses Infobric at work today 23 (46.0%); Has never heard of Infobric 18 (36.0%); Has heard the name but knows nothing more 6 (12.0%); Has seen Infobric equipment or the logo on a site 3 (6.0%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 30 of 50 = **60.0%**
- Would keep reading (`would_continue`): no 30, yes 20
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Finance or administration | 14 | 64.3% | 35.7% |
| Fleet, equipment or rental manager | 10 | 40.0% | 60.0% |
| Not a target visitor | 7 | 85.7% | 14.3% |
| Owner or senior manager | 7 | 71.4% | 28.6% |
| Supervisor or daily user | 6 | 50.0% | 50.0% |
| Operations, project or site manager | 5 | 60.0% | 40.0% |
| HSE or compliance | 1 | 0.0% | 100.0% |

| Traffic segment | n | left early | would continue = yes | next step: leave | go to login |
|---|---:|---:|---:|---:|---:|
| Existing customer (login or support) | 23 | 100.0% | 0.0% | 0.0% | 100.0% |
| Prospect (evaluating a supplier) | 20 | 5.0% | 95.0% | 5.0% | 0.0% |
| Job seeker | 3 | 100.0% | 0.0% | 100.0% | 0.0% |
| Mis-click from a search result or an ad | 2 | 100.0% | 0.0% | 100.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 1 | 100.0% | 0.0% | 100.0% | 0.0% |
| Student or researcher | 1 | 0.0% | 100.0% | 100.0% | 0.0% |

## 3b. Trust as a ladder of commitments (yes/no, rising cost) plus one belief item

- **Would give a work email for a guide**: yes 26.0% of 50
- **Would ask for a call-back**: yes 8.0% of 50
- **Would book a demo this week**: yes 2.0% of 50
- **Would run a pilot on own data this month**: yes 0.0% of 50
- **Would accept the proof claim unchecked**: yes 64.0% of 50
- **Rungs accepted (0-4)**: mean 0.36, sd 0.66, distribution 0: 37, 1: 8, 2: 5, 3: 0, 4: 0; inconsistent ladders (a yes above a no) 1 of 50
- η² by visitor kind 0.18 · by traffic segment 0.45 · by visit intent 0.64

| Group | n | mean rungs | give a work email for a guide | ask for a call-back | book a demo this week | run a pilot on own data this month | accept the proof claim unchecked |
|---|---:|---:|---:|---:|---:|---:|---:|
| Existing customer (login or support) | 23 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Prospect (evaluating a supplier) | 20 | 0.90 | 65.0% | 20.0% | 5.0% | 0.0% | 40.0% |
| Job seeker | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Mis-click from a search result or an ad | 2 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Student or researcher | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Finance or administration | 14 | 0.21 | 21.4% | 0.0% | 0.0% | 0.0% | 78.6% |
| Fleet, equipment or rental manager | 10 | 0.80 | 50.0% | 30.0% | 0.0% | 0.0% | 70.0% |
| Not a target visitor | 7 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 14.3% |
| Owner or senior manager | 7 | 0.43 | 28.6% | 14.3% | 0.0% | 0.0% | 71.4% |
| Supervisor or daily user | 6 | 0.17 | 16.7% | 0.0% | 0.0% | 0.0% | 83.3% |
| Operations, project or site manager | 5 | 0.40 | 20.0% | 0.0% | 20.0% | 0.0% | 60.0% |
| HSE or compliance | 1 | 1.00 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Existing customer: came to log in or reach support, not to evaluate | 23 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Has a specific problem to solve right now | 13 | 1.23 | 84.6% | 30.8% | 7.7% | 0.0% | 46.2% |
| Exploring ways to improve operations | 7 | 0.29 | 28.6% | 0.0% | 0.0% | 0.0% | 28.6% |
| Looking for job openings at Infobric | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Landed here by mistake from a search result or an ad | 2 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Wants to sell services or products to Infobric | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Researching the company for a school or university assignment | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 50 | 4.20 | 0.53 | 0.0% | 0.0% | 6.0% | 68.0% | 26.0% |  |
| language_relevance | 50 | 3.20 | 1.00 | 12.0% | 6.0% | 32.0% | 50.0% | 0.0% |  |
| practical_value | 50 | 2.68 | 0.76 | 12.0% | 14.0% | 68.0% | 6.0% | 0.0% |  |
| trust | 50 | 3.36 | 0.52 | 0.0% | 2.0% | 60.0% | 38.0% | 0.0% |  |
| next_step_confidence | 48 | 3.46 | 0.91 | 6.2% | 2.1% | 39.6% | 43.8% | 8.3% |  |
| next_step_ease | 20 | 3.85 | 0.36 | 0.0% | 0.0% | 15.0% | 85.0% | 0.0% |  |
| cta_match | 20 | 3.95 | 0.38 | 0.0% | 0.0% | 10.0% | 85.0% | 5.0% |  |
| contact_likelihood | 50 | 1.86 | 0.94 | 44.0% | 34.0% | 14.0% | 8.0% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Finance or administration | 14 | 4.21 | 3.21 | 2.79 | 3.43 | 3.71 | 3.80 | 3.80 | 1.71 |
| Fleet, equipment or rental manager | 10 | 4.20 | 3.60 | 3.10 | 3.30 | 3.70 | 3.83 | 3.83 | 2.50 |
| Not a target visitor | 7 | 3.86 | 1.14 | 1.14 | 2.86 | 2.00 | 4.00 | 5.00 | 1.14 |
| Owner or senior manager | 7 | 4.14 | 3.43 | 2.71 | 3.43 | 3.29 | 4.00 | 4.00 | 2.00 |
| Supervisor or daily user | 6 | 4.50 | 4.00 | 3.17 | 3.67 | 4.00 | 4.00 | 4.00 | 1.67 |
| Operations, project or site manager | 5 | 4.40 | 3.80 | 3.00 | 3.60 | 3.40 | 3.50 | 4.00 | 1.80 |
| HSE or compliance | 1 | 4.00 | 4.00 | 3.00 | 3.00 | 3.00 | 4.00 | 4.00 | 3.00 |

## 5. What they would do next

- **Next step**: go_to_login 23 (46.0%); learn_more 14 (28.0%); leave 8 (16.0%); contact_sales 4 (8.0%); book_demo 1 (2.0%)
- **Needed before going further**: would_not_proceed 31 (62.0%); need_references_first 18 (36.0%); need_pilot_first 1 (2.0%)
- **Main basis of the decision**: fit 21 (42.0%); other 15 (30.0%); support 10 (20.0%); consolidation 1 (2.0%); legal_compliance 1 (2.0%); features 1 (2.0%); integrations 1 (2.0%)
- Converted (contact / demo / trial as the next step): 5 of 50 = 10.0%
- Information they missed most: price 19; integrations 15; setup_time 15; references 14; hardware 4; data_privacy 2
- Weakest part of the page: unknown 20, top 18, middle 11, bottom 1 · strongest: top 24, middle 14, unknown 11, bottom 1

| Visitor kind | go_to_login | learn_more | leave | contact_sales | book_demo |
|---|---:|---:|---:|---:|---:|
| Finance or administration | 64.3% | 35.7% | 0.0% | 0.0% | 0.0% |
| Fleet, equipment or rental manager | 40.0% | 30.0% | 0.0% | 30.0% | 0.0% |
| Not a target visitor | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% |
| Owner or senior manager | 57.1% | 14.3% | 14.3% | 14.3% | 0.0% |
| Supervisor or daily user | 50.0% | 50.0% | 0.0% | 0.0% | 0.0% |
| Operations, project or site manager | 60.0% | 20.0% | 0.0% | 0.0% | 20.0% |
| HSE or compliance | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 50
- Grounding: quoted claims found on the page 0.985, quoted phrases found on the page 0.971; trials with any ungrounded quote 5 of 50
- Primary button: inspected 40.0%, landed on the expected page 100.0%, label quoted correctly 100.0%
