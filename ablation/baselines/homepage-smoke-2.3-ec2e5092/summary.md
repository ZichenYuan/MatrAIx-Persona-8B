# homepage: 50 of 50 trials finished — pg-web-infobric-audit-v2-homepage-ec2e5092

## 1. Coverage (pipeline health — gate, not a result)

- Launched 50, finished 50, passed verifier 49 (98.0%), failed 1
  - 1 × NonZeroAgentExitCodeError
- Artifact parse: clean 49 (clean rate 100.0%)
- Instrument ['2.3'], variant ['full'], device {'desktop': 49}
- Values the verifier could not map onto the answer set: 2 across 2 trials

## 2. Who was simulated (finished trials)

- **traffic_segment**: Existing customer (login or support) 22 (44.9%); Prospect (evaluating a supplier) 20 (40.8%); Job seeker 3 (6.1%); Mis-click from a search result or an ad 2 (4.1%); Supplier or partner (selling to Infobric) 1 (2.0%); Student or researcher 1 (2.0%)
- **audience_group**: Supervisor or daily user 15 (30.6%); Finance or administration 12 (24.5%); Fleet, equipment or rental manager 8 (16.3%); Operations, project or site manager 8 (16.3%); Owner or senior manager 6 (12.2%)
- **tier**: Vehicle and field service business 14 (28.6%); Subcontractor 12 (24.5%); Rental 11 (22.4%); Main contractor 6 (12.2%); Developer 6 (12.2%)
- **visit_intent**: Existing customer: came to log in or reach support, not to evaluate 22 (44.9%); Has a specific problem to solve right now 13 (26.5%); Exploring ways to improve operations 7 (14.3%); Looking for job openings at Infobric 3 (6.1%); Landed here by mistake from a search result or an ad 2 (4.1%); Wants to sell services or products to Infobric 1 (2.0%); Researching the company for a school or university assignment 1 (2.0%)
- **infobric_familiarity**: Uses Infobric at work today 22 (44.9%); Has never heard of Infobric 14 (28.6%); Has heard the name but knows nothing more 12 (24.5%); Has seen Infobric equipment or the logo on a site 1 (2.0%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 6 of 49 = **12.2%**
- Would keep reading (`would_continue`): yes 43, no 6
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Supervisor or daily user | 15 | 13.3% | 86.7% |
| Finance or administration | 12 | 8.3% | 91.7% |
| Fleet, equipment or rental manager | 8 | 25.0% | 75.0% |
| Operations, project or site manager | 8 | 12.5% | 87.5% |
| Owner or senior manager | 6 | 0.0% | 100.0% |

| Traffic segment | n | left early | would continue = yes | next step: leave | go to login |
|---|---:|---:|---:|---:|---:|
| Existing customer (login or support) | 22 | 27.3% | 72.7% | 0.0% | 100.0% |
| Prospect (evaluating a supplier) | 20 | 0.0% | 100.0% | 0.0% | 0.0% |
| Job seeker | 3 | 0.0% | 100.0% | 0.0% | 0.0% |
| Mis-click from a search result or an ad | 2 | 0.0% | 100.0% | 0.0% | 0.0% |
| Supplier or partner (selling to Infobric) | 1 | 0.0% | 100.0% | 0.0% | 0.0% |
| Student or researcher | 1 | 0.0% | 100.0% | 0.0% | 0.0% |

## 3b. Trust as three concrete acts (yes/no)

- **Would enter company details in the form today**: yes 0.0% of 49
- **Would accept the proof claim unchecked**: yes 6.1% of 49
- **Would mention the supplier to a colleague**: yes 87.8% of 49 (2 unanswered)
- **Yes-count (0-3)**: mean 0.98, sd 0.33, distribution 0: 3, 1: 42, 2: 2, 3: 0
- η² by visitor kind: 0.01

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 49 | 4.06 | 0.24 | 0.0% | 0.0% | 0.0% | 93.9% | 6.1% | **collapsed** (sd < 0.3) |
| language_relevance | 47 | 3.72 | 0.49 | 0.0% | 2.1% | 23.4% | 74.5% | 0.0% |  |
| practical_value | 47 | 3.49 | 0.65 | 0.0% | 8.5% | 34.0% | 57.4% | 0.0% |  |
| trust | 47 | 3.00 | 0.00 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | **collapsed** (sd < 0.3) |
| next_step_confidence | 47 | 3.96 | 0.50 | 0.0% | 2.1% | 8.5% | 80.9% | 8.5% |  |
| next_step_ease | 43 | 3.81 | 0.54 | 0.0% | 0.0% | 25.6% | 67.4% | 7.0% |  |
| cta_match | 43 | 4.51 | 0.50 | 0.0% | 0.0% | 0.0% | 48.8% | 51.2% |  |
| contact_likelihood | 49 | 2.08 | 1.16 | 49.0% | 8.2% | 28.6% | 14.3% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Supervisor or daily user | 15 | 4.07 | 3.80 | 3.40 | 3.00 | 3.93 | 3.54 | 4.46 | 1.93 |
| Finance or administration | 12 | 4.08 | 3.33 | 3.25 | 3.00 | 4.08 | 3.91 | 4.36 | 2.33 |
| Fleet, equipment or rental manager | 8 | 4.00 | 3.86 | 3.57 | 3.00 | 3.57 | 4.00 | 4.50 | 2.50 |
| Operations, project or site manager | 8 | 4.00 | 4.00 | 3.86 | 3.00 | 4.14 | 4.00 | 4.71 | 1.62 |
| Owner or senior manager | 6 | 4.17 | 3.83 | 3.67 | 3.00 | 4.00 | 3.83 | 4.67 | 2.00 |

## 5. What they would do next

- **Next step**: go_to_login 22 (44.9%); learn_more 15 (30.6%); contact_sales 8 (16.3%); come_back_later 4 (8.2%)
- **Needed before going further**: need_references_first 42 (85.7%); would_not_proceed 6 (12.2%); need_pilot_first 1 (2.0%)
- **Main basis of the decision**: fit 36 (73.5%); support 12 (24.5%); integrations 1 (2.0%)
- Converted (contact / demo / trial as the next step): 8 of 49 = 16.3%
- Information they missed most: price 44; integrations 44; setup_time 44; data_privacy 44; contract_terms 44; references 43; hardware 34
- Weakest part of the page: middle 24, top 22, bottom 2, unknown 1 · strongest: top 28, middle 19, unknown 2

| Visitor kind | go_to_login | learn_more | contact_sales | come_back_later |
|---|---:|---:|---:|---:|
| Supervisor or daily user | 46.7% | 46.7% | 0.0% | 6.7% |
| Finance or administration | 33.3% | 33.3% | 33.3% | 0.0% |
| Fleet, equipment or rental manager | 50.0% | 0.0% | 50.0% | 0.0% |
| Operations, project or site manager | 50.0% | 25.0% | 0.0% | 25.0% |
| Owner or senior manager | 50.0% | 33.3% | 0.0% | 16.7% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 49
- Grounding: quoted claims found on the page 0.971, quoted phrases found on the page 0.960; trials with any ungrounded quote 16 of 49
- Primary button: inspected 87.8%, landed on the expected page 100.0%, label quoted correctly 100.0%
