# homepage: 834 of 1000 trials finished — pg-web-infobric-audit-v2-homepage-3fffd213

## 1. Coverage (pipeline health — gate, not a result)

- Launched 1000, finished 834, passed verifier 785 (94.1%), failed 49
  - 49 × NonZeroAgentExitCodeError
- Artifact parse: clean 766, repaired_unterminated_string 11, repaired_syntax 5, repaired_inner_quotes 2, repaired_trailing_data 1 (clean rate 97.6%)
- Instrument ['2.2'], variant ['full'], device {'desktop': 785}
- Values the verifier could not map onto the answer set: 0 across 0 trials

## 2. Who was simulated (finished trials)

- **audience_group**: Supervisor or daily user 213 (27.1%); Finance or administration 206 (26.2%); Fleet, equipment or rental manager 117 (14.9%); Operations, project or site manager 114 (14.5%); Owner or senior manager 95 (12.1%); HSE or compliance 40 (5.1%)
- **tier**: Rental 184 (23.4%); Subcontractor 169 (21.5%); Vehicle and field service business 168 (21.4%); Main contractor 159 (20.3%); Developer 105 (13.4%)
- **visit_intent**: Has a specific problem to solve right now 398 (50.7%); Exploring ways to improve operations 387 (49.3%)
- **infobric_familiarity**: Has never heard of Infobric 442 (56.3%); Has heard the name but knows nothing more 232 (29.6%); Has seen Infobric equipment or the logo on a site 111 (14.1%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 0 of 785 = **0.0%**
- Would keep reading (`would_continue`): yes 785
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Supervisor or daily user | 213 | 0.0% | 100.0% |
| Finance or administration | 206 | 0.0% | 100.0% |
| Fleet, equipment or rental manager | 117 | 0.0% | 100.0% |
| Operations, project or site manager | 114 | 0.0% | 100.0% |
| Owner or senior manager | 95 | 0.0% | 100.0% |
| HSE or compliance | 40 | 0.0% | 100.0% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 785 | 4.01 | 0.12 | 0.0% | 0.0% | 0.0% | 98.6% | 1.4% | **collapsed** (sd < 0.3) |
| language_relevance | 785 | 4.00 | 0.24 | 0.0% | 0.0% | 2.9% | 94.4% | 2.7% | **collapsed** (sd < 0.3) |
| practical_value | 785 | 3.67 | 0.47 | 0.0% | 0.0% | 33.0% | 67.0% | 0.0% |  |
| trust | 785 | 3.00 | 0.00 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | **collapsed** (sd < 0.3) |
| next_step_confidence | 785 | 3.88 | 0.32 | 0.0% | 0.0% | 11.6% | 88.4% | 0.0% |  |
| next_step_ease | 784 | 3.90 | 0.30 | 0.0% | 0.0% | 10.2% | 89.8% | 0.0% |  |
| cta_match | 785 | 4.60 | 0.49 | 0.0% | 0.0% | 0.0% | 40.0% | 60.0% |  |
| contact_likelihood | 785 | 2.83 | 0.64 | 0.0% | 30.4% | 55.7% | 13.9% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Supervisor or daily user | 213 | 4.02 | 4.00 | 3.68 | 3.00 | 3.88 | 3.90 | 4.62 | 2.75 |
| Finance or administration | 206 | 4.00 | 3.93 | 3.56 | 3.00 | 3.88 | 3.89 | 4.57 | 2.80 |
| Fleet, equipment or rental manager | 117 | 4.00 | 4.01 | 3.63 | 3.00 | 3.88 | 3.87 | 4.59 | 2.94 |
| Operations, project or site manager | 114 | 4.02 | 4.05 | 3.82 | 3.00 | 3.88 | 3.92 | 4.60 | 2.92 |
| Owner or senior manager | 95 | 4.02 | 4.08 | 3.85 | 3.00 | 3.87 | 3.93 | 4.56 | 3.02 |
| HSE or compliance | 40 | 4.05 | 3.98 | 3.45 | 3.00 | 3.95 | 3.90 | 4.80 | 2.48 |

## 4b. In-browse vs scored after the visit (Finding 1 replication)

107 of 785 trials re-scored outside the browser by the same model from the persona text plus the persona's own notes (application/scripts/score_audit.py). η² = share of score variance explained by the persona dimension; 0.01 small, 0.06 medium, 0.14 large.

| Score | mean in-browse | sd | mean scored | sd | η² visitor kind (in / scored) | η² tier (in / scored) | η² visit intent (in / scored) | values used (scored) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 4.01 | 0.10 | 4.23 | 0.42 | 0.02 / 0.10 | 0.03 / 0.03 | 0.01 / 0.00 | [4, 5] |
| language_relevance | 4.01 | 0.10 | 4.47 | 0.50 | 0.06 / 0.04 | 0.04 / 0.23 | 0.01 / 0.07 | [4, 5] |
| practical_value | 3.71 | 0.45 | 3.59 | 0.49 | 0.07 / 0.04 | 0.02 / 0.03 | 0.03 / 0.02 | [3, 4] |
| trust | 3.00 | 0.00 | 2.99 | 0.10 | 0.00 / 0.02 | 0.00 / 0.04 | 0.00 / 0.01 | [2, 3] |
| next_step_confidence | 3.84 | 0.37 | 3.99 | 0.35 | 0.02 / 0.04 | 0.01 / 0.05 | 0.02 / 0.02 | [2, 3, 4, 5] |
| next_step_ease | 3.82 | 0.38 | 3.69 | 0.46 | 0.03 / 0.04 | 0.03 / 0.08 | 0.01 / 0.00 | [3, 4] |
| cta_match | 4.66 | 0.47 | 4.34 | 0.56 | 0.04 / 0.08 | 0.02 / 0.04 | 0.00 / 0.03 | [3, 4, 5] |
| contact_likelihood | 2.81 | 0.64 | 2.80 | 0.62 | 0.04 / 0.05 | 0.02 / 0.06 | 0.39 / 0.30 | [2, 3, 4] |

### Scored after the visit, by visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Supervisor or daily user | 32 | 4.22 | 4.50 | 3.62 | 2.97 | 4.00 | 3.66 | 4.25 | 2.75 |
| Finance or administration | 21 | 4.38 | 4.38 | 3.71 | 3.00 | 4.10 | 3.76 | 4.48 | 2.95 |
| Fleet, equipment or rental manager | 17 | 4.00 | 4.47 | 3.41 | 3.00 | 3.88 | 3.53 | 4.24 | 2.71 |
| Operations, project or site manager | 18 | 4.17 | 4.44 | 3.61 | 3.00 | 3.94 | 3.78 | 4.17 | 3.00 |
| Owner or senior manager | 14 | 4.36 | 4.64 | 3.50 | 3.00 | 4.00 | 3.79 | 4.50 | 2.64 |
| HSE or compliance | 5 | 4.40 | 4.20 | 3.60 | 3.00 | 4.00 | 3.60 | 4.80 | 2.60 |

## 5. What they would do next

- **Next step**: contact_sales 299 (38.1%); come_back_later 286 (36.4%); learn_more 200 (25.5%)
- **Needed before going further**: need_references_first 754 (96.1%); need_pilot_first 31 (3.9%)
- **Main basis of the decision**: fit 780 (99.4%); consolidation 3 (0.4%); integrations 2 (0.3%)
- Converted (contact / demo / trial as the next step): 299 of 785 = 38.1%
- Information they missed most: price 785; setup_time 785; references 785; integrations 784; data_privacy 783; contract_terms 775; hardware 588
- Weakest part of the page: middle 462, bottom 163, top 158, unknown 2 · strongest: middle 429, top 355, bottom 1

| Visitor kind | contact_sales | come_back_later | learn_more |
|---|---:|---:|---:|
| Supervisor or daily user | 34.3% | 36.6% | 29.1% |
| Finance or administration | 35.9% | 35.0% | 29.1% |
| Fleet, equipment or rental manager | 41.0% | 36.8% | 22.2% |
| Operations, project or site manager | 43.9% | 35.1% | 21.1% |
| Owner or senior manager | 45.3% | 35.8% | 18.9% |
| HSE or compliance | 27.5% | 47.5% | 25.0% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 785
- Grounding: quoted claims found on the page 0.962, quoted phrases found on the page 0.967; trials with any ungrounded quote 291 of 785
- Primary button: inspected 100.0%, landed on the expected page 100.0%, label quoted correctly 100.0%

