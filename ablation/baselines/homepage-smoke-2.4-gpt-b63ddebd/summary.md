# homepage: 49 of 50 trials finished — pg-web-infobric-audit-v2-homepage-b63ddebd

## 1. Coverage (pipeline health — gate, not a result)

- Launched 50, finished 49, passed verifier 49 (100.0%), failed 0
- Artifact parse: clean 49 (clean rate 100.0%)
- Instrument ['2.4'], variant ['full'], device {'desktop': 49}
- Values the verifier could not map onto the answer set: 0 across 0 trials

## 2. Who was simulated (finished trials)

- **traffic_segment**: Existing customer (login or support) 22 (44.9%); Prospect (evaluating a supplier) 20 (40.8%); Job seeker 3 (6.1%); Mis-click from a search result or an ad 2 (4.1%); Student or researcher 1 (2.0%); Supplier or partner (selling to Infobric) 1 (2.0%)
- **audience_group**: Finance or administration 13 (26.5%); Fleet, equipment or rental manager 10 (20.4%); Owner or senior manager 7 (14.3%); Not a target visitor 7 (14.3%); Supervisor or daily user 6 (12.2%); Operations, project or site manager 5 (10.2%); HSE or compliance 1 (2.0%)
- **tier**: Main contractor 11 (22.4%); Subcontractor 10 (20.4%); Rental 10 (20.4%); Vehicle and field service business 8 (16.3%); Not applicable 7 (14.3%); Developer 3 (6.1%)
- **visit_intent**: Existing customer: came to log in or reach support, not to evaluate 22 (44.9%); Has a specific problem to solve right now 13 (26.5%); Exploring ways to improve operations 7 (14.3%); Looking for job openings at Infobric 3 (6.1%); Landed here by mistake from a search result or an ad 2 (4.1%); Researching the company for a school or university assignment 1 (2.0%); Wants to sell services or products to Infobric 1 (2.0%)
- **infobric_familiarity**: Uses Infobric at work today 22 (44.9%); Has never heard of Infobric 18 (36.7%); Has heard the name but knows nothing more 6 (12.2%); Has seen Infobric equipment or the logo on a site 3 (6.1%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 27 of 49 = **55.1%**
- Would keep reading (`would_continue`): no 27, yes 22
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Finance or administration | 13 | 53.8% | 46.2% |
| Fleet, equipment or rental manager | 10 | 40.0% | 60.0% |
| Owner or senior manager | 7 | 57.1% | 42.9% |
| Not a target visitor | 7 | 85.7% | 14.3% |
| Supervisor or daily user | 6 | 50.0% | 50.0% |
| Operations, project or site manager | 5 | 60.0% | 40.0% |
| HSE or compliance | 1 | 0.0% | 100.0% |

| Traffic segment | n | left early | would continue = yes | next step: leave | go to login |
|---|---:|---:|---:|---:|---:|
| Existing customer (login or support) | 22 | 95.5% | 4.5% | 0.0% | 100.0% |
| Prospect (evaluating a supplier) | 20 | 0.0% | 100.0% | 0.0% | 0.0% |
| Job seeker | 3 | 100.0% | 0.0% | 33.3% | 0.0% |
| Mis-click from a search result or an ad | 2 | 100.0% | 0.0% | 100.0% | 0.0% |
| Student or researcher | 1 | 0.0% | 100.0% | 0.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 1 | 100.0% | 0.0% | 100.0% | 0.0% |

## 3b. Trust as a ladder of commitments (yes/no, rising cost) plus one belief item

- **Would give a work email for a guide**: yes 40.8% of 49
- **Would ask for a call-back**: yes 16.3% of 49
- **Would book a demo this week**: yes 0.0% of 49
- **Would run a pilot on own data this month**: yes 0.0% of 49
- **Would accept the proof claim unchecked**: yes 16.3% of 49
- **Rungs accepted (0-4)**: mean 0.57, sd 0.76, distribution 0: 29, 1: 12, 2: 8, 3: 0, 4: 0; inconsistent ladders (a yes above a no) 0 of 49
- η² by visitor kind 0.13 · by traffic segment 0.83 · by visit intent 0.89

| Group | n | mean rungs | give a work email for a guide | ask for a call-back | book a demo this week | run a pilot on own data this month | accept the proof claim unchecked |
|---|---:|---:|---:|---:|---:|---:|---:|
| Existing customer (login or support) | 22 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 31.8% |
| Prospect (evaluating a supplier) | 20 | 1.40 | 100.0% | 40.0% | 0.0% | 0.0% | 0.0% |
| Job seeker | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Mis-click from a search result or an ad | 2 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Student or researcher | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| Finance or administration | 13 | 0.54 | 38.5% | 15.4% | 0.0% | 0.0% | 7.7% |
| Fleet, equipment or rental manager | 10 | 0.90 | 60.0% | 30.0% | 0.0% | 0.0% | 20.0% |
| Owner or senior manager | 7 | 0.71 | 42.9% | 28.6% | 0.0% | 0.0% | 14.3% |
| Not a target visitor | 7 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 14.3% |
| Supervisor or daily user | 6 | 0.50 | 50.0% | 0.0% | 0.0% | 0.0% | 50.0% |
| Operations, project or site manager | 5 | 0.60 | 40.0% | 20.0% | 0.0% | 0.0% | 0.0% |
| HSE or compliance | 1 | 1.00 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Existing customer: came to log in or reach support, not to evaluate | 22 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 31.8% |
| Has a specific problem to solve right now | 13 | 1.62 | 100.0% | 61.5% | 0.0% | 0.0% | 0.0% |
| Exploring ways to improve operations | 7 | 1.00 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Looking for job openings at Infobric | 3 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Landed here by mistake from a search result or an ad | 2 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Researching the company for a school or university assignment | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Wants to sell services or products to Infobric | 1 | 0.00 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 48 | 3.90 | 0.42 | 0.0% | 0.0% | 14.6% | 81.2% | 4.2% |  |
| language_relevance | 48 | 3.27 | 1.06 | 12.5% | 6.2% | 25.0% | 54.2% | 2.1% |  |
| practical_value | 47 | 2.60 | 1.10 | 21.3% | 25.5% | 25.5% | 27.7% | 0.0% |  |
| trust | 48 | 2.71 | 0.54 | 4.2% | 20.8% | 75.0% | 0.0% | 0.0% |  |
| next_step_confidence | 48 | 3.79 | 1.17 | 12.5% | 0.0% | 6.2% | 58.3% | 22.9% |  |
| next_step_ease | 22 | 3.95 | 0.21 | 0.0% | 0.0% | 4.5% | 95.5% | 0.0% | **collapsed** (sd < 0.3) |
| cta_match | 22 | 4.50 | 0.50 | 0.0% | 0.0% | 0.0% | 50.0% | 50.0% |  |
| contact_likelihood | 49 | 2.04 | 1.24 | 57.1% | 0.0% | 24.5% | 18.4% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Finance or administration | 13 | 3.92 | 3.46 | 2.62 | 2.77 | 4.31 | 4.00 | 4.33 | 1.92 |
| Fleet, equipment or rental manager | 10 | 3.80 | 3.40 | 2.80 | 2.70 | 4.00 | 3.83 | 4.83 | 2.60 |
| Owner or senior manager | 7 | 4.00 | 4.00 | 3.00 | 3.00 | 4.33 | 4.00 | 4.33 | 2.14 |
| Not a target visitor | 7 | 4.14 | 1.29 | 1.29 | 1.86 | 1.29 | 4.00 | 4.00 | 1.29 |
| Supervisor or daily user | 6 | 3.83 | 3.83 | 3.20 | 3.00 | 4.17 | 4.00 | 4.33 | 2.00 |
| Operations, project or site manager | 5 | 3.60 | 3.60 | 2.80 | 3.00 | 4.40 | 4.00 | 4.50 | 2.00 |
| HSE or compliance | 1 | 4.00 | 4.00 | 3.00 | 3.00 | 4.00 | 4.00 | 5.00 | 3.00 |

## 5. What they would do next

- **Next step**: go_to_login 22 (44.9%); contact_sales 14 (28.6%); go_elsewhere_on_site 5 (10.2%); come_back_later 4 (8.2%); leave 4 (8.2%)
- **Needed before going further**: would_not_proceed 29 (59.2%); need_references_first 20 (40.8%)
- **Main basis of the decision**: fit 40 (81.6%); support 7 (14.3%); other 2 (4.1%)
- Converted (contact / demo / trial as the next step): 14 of 49 = 28.6%
- Information they missed most: data_privacy 31; integrations 30; price 29; setup_time 29; references 29; contract_terms 28; hardware 13
- Weakest part of the page: top 31, middle 11, unknown 4, bottom 3 · strongest: top 41, middle 7, unknown 1

| Visitor kind | go_to_login | contact_sales | go_elsewhere_on_site | come_back_later | leave |
|---|---:|---:|---:|---:|---:|
| Finance or administration | 61.5% | 30.8% | 0.0% | 7.7% | 0.0% |
| Fleet, equipment or rental manager | 40.0% | 40.0% | 0.0% | 20.0% | 0.0% |
| Owner or senior manager | 57.1% | 42.9% | 0.0% | 0.0% | 0.0% |
| Not a target visitor | 0.0% | 0.0% | 42.9% | 0.0% | 57.1% |
| Supervisor or daily user | 50.0% | 16.7% | 16.7% | 16.7% | 0.0% |
| Operations, project or site manager | 60.0% | 20.0% | 20.0% | 0.0% | 0.0% |
| HSE or compliance | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 49
- Grounding: quoted claims found on the page 0.995, quoted phrases found on the page 0.983; trials with any ungrounded quote 6 of 49
- Primary button: inspected 44.9%, landed on the expected page 100.0%, label quoted correctly 100.0%
