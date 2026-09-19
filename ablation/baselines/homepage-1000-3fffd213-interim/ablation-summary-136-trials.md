# homepage: 145 of 1000 trials finished — pg-web-infobric-audit-v2-homepage-3fffd213

## 1. Coverage (pipeline health — gate, not a result)

- Launched 1000, finished 145, passed verifier 136 (93.8%), failed 9
  - 7 × NonZeroAgentExitCodeError
  - 2 × verifier scored 0 (no exception)
- Artifact parse: clean 135, repaired_unterminated_string 1 (clean rate 99.3%)
- Instrument ['2.2'], variant ['full'], device {'desktop': 136}
- Values the verifier could not map onto the answer set: 0 across 0 trials

## 2. Who was simulated (finished trials)

- **audience_group**: Supervisor or daily user 42 (30.9%); Finance or administration 29 (21.3%); Operations, project or site manager 21 (15.4%); Owner or senior manager 19 (14.0%); Fleet, equipment or rental manager 18 (13.2%); HSE or compliance 7 (5.1%)
- **tier**: Subcontractor 33 (24.3%); Rental 31 (22.8%); Vehicle and field service business 26 (19.1%); Main contractor 26 (19.1%); Developer 20 (14.7%)
- **visit_intent**: Exploring ways to improve operations 68 (50.0%); Has a specific problem to solve right now 68 (50.0%)
- **infobric_familiarity**: Has never heard of Infobric 74 (54.4%); Has heard the name but knows nothing more 48 (35.3%); Has seen Infobric equipment or the logo on a site 14 (10.3%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 0 of 136 = **0.0%**
- Would keep reading (`would_continue`): yes 136
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Supervisor or daily user | 42 | 0.0% | 100.0% |
| Finance or administration | 29 | 0.0% | 100.0% |
| Operations, project or site manager | 21 | 0.0% | 100.0% |
| Owner or senior manager | 19 | 0.0% | 100.0% |
| Fleet, equipment or rental manager | 18 | 0.0% | 100.0% |
| HSE or compliance | 7 | 0.0% | 100.0% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 136 | 4.01 | 0.09 | 0.0% | 0.0% | 0.0% | 99.3% | 0.7% | **collapsed** (sd < 0.3) |
| language_relevance | 136 | 4.00 | 0.21 | 0.0% | 0.0% | 2.2% | 95.6% | 2.2% | **collapsed** (sd < 0.3) |
| practical_value | 136 | 3.69 | 0.46 | 0.0% | 0.0% | 30.9% | 69.1% | 0.0% |  |
| trust | 136 | 3.00 | 0.00 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | **collapsed** (sd < 0.3) |
| next_step_confidence | 136 | 3.85 | 0.35 | 0.0% | 0.0% | 14.7% | 85.3% | 0.0% |  |
| next_step_ease | 136 | 3.85 | 0.36 | 0.0% | 0.0% | 15.4% | 84.6% | 0.0% |  |
| cta_match | 136 | 4.65 | 0.48 | 0.0% | 0.0% | 0.0% | 34.6% | 65.4% |  |
| contact_likelihood | 136 | 2.81 | 0.65 | 0.0% | 32.4% | 54.4% | 13.2% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Supervisor or daily user | 42 | 4.02 | 3.98 | 3.64 | 3.00 | 3.86 | 3.88 | 4.74 | 2.69 |
| Finance or administration | 29 | 4.00 | 3.93 | 3.55 | 3.00 | 3.90 | 3.86 | 4.55 | 2.76 |
| Operations, project or site manager | 21 | 4.00 | 4.05 | 3.86 | 3.00 | 3.76 | 3.90 | 4.62 | 3.00 |
| Owner or senior manager | 19 | 4.00 | 4.11 | 3.84 | 3.00 | 3.84 | 3.79 | 4.63 | 2.89 |
| Fleet, equipment or rental manager | 18 | 4.00 | 4.00 | 3.72 | 3.00 | 3.83 | 3.72 | 4.61 | 2.89 |
| HSE or compliance | 7 | 4.00 | 4.00 | 3.57 | 3.00 | 4.00 | 3.86 | 4.86 | 2.71 |

## 4b. In-browse vs scored after the visit (Finding 1 replication)

107 of 136 trials re-scored outside the browser by the same model from the persona text plus the persona's own notes (application/scripts/score_audit.py). η² = share of score variance explained by the persona dimension; 0.01 small, 0.06 medium, 0.14 large.

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
| Operations, project or site manager | 18 | 4.17 | 4.44 | 3.61 | 3.00 | 3.94 | 3.78 | 4.17 | 3.00 |
| Owner or senior manager | 14 | 4.36 | 4.64 | 3.50 | 3.00 | 4.00 | 3.79 | 4.50 | 2.64 |
| Fleet, equipment or rental manager | 17 | 4.00 | 4.47 | 3.41 | 3.00 | 3.88 | 3.53 | 4.24 | 2.71 |
| HSE or compliance | 5 | 4.40 | 4.20 | 3.60 | 3.00 | 4.00 | 3.60 | 4.80 | 2.60 |

## 5. What they would do next

- **Next step**: come_back_later 60 (44.1%); contact_sales 48 (35.3%); learn_more 28 (20.6%)
- **Needed before going further**: need_references_first 128 (94.1%); need_pilot_first 8 (5.9%)
- **Main basis of the decision**: fit 135 (99.3%); integrations 1 (0.7%)
- Converted (contact / demo / trial as the next step): 48 of 136 = 35.3%
- Information they missed most: price 136; integrations 136; setup_time 136; references 136; data_privacy 136; contract_terms 135; hardware 106
- Weakest part of the page: middle 76, top 31, bottom 29 · strongest: middle 75, top 60, bottom 1

| Visitor kind | come_back_later | contact_sales | learn_more |
|---|---:|---:|---:|
| Supervisor or daily user | 45.2% | 31.0% | 23.8% |
| Finance or administration | 37.9% | 41.4% | 20.7% |
| Operations, project or site manager | 38.1% | 42.9% | 19.0% |
| Owner or senior manager | 42.1% | 36.8% | 21.1% |
| Fleet, equipment or rental manager | 61.1% | 27.8% | 11.1% |
| HSE or compliance | 42.9% | 28.6% | 28.6% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 136
- Grounding: quoted claims found on the page 0.966, quoted phrases found on the page 0.969; trials with any ungrounded quote 55 of 136
- Primary button: inspected 100.0%, landed on the expected page 100.0%, label quoted correctly 100.0%
