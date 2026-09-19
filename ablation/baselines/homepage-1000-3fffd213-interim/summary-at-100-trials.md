# homepage: 102 of 1000 trials finished — pg-web-infobric-audit-v2-homepage-3fffd213

## 1. Coverage (pipeline health — gate, not a result)

- Launched 1000, finished 102, passed verifier 95 (93.1%), failed 7
  - 5 × NonZeroAgentExitCodeError
  - 2 × verifier scored 0 (no exception)
- Artifact parse: clean 94, repaired_unterminated_string 1 (clean rate 98.9%)
- Instrument ['2.2'], variant ['full'], device {'desktop': 95}
- Values the verifier could not map onto the answer set: 0 across 0 trials

## 2. Who was simulated (finished trials)

- **audience_group**: Supervisor or daily user 28 (29.5%); Finance or administration 20 (21.1%); Fleet, equipment or rental manager 15 (15.8%); Operations, project or site manager 14 (14.7%); Owner or senior manager 13 (13.7%); HSE or compliance 5 (5.3%)
- **tier**: Rental 24 (25.3%); Subcontractor 23 (24.2%); Main contractor 18 (18.9%); Vehicle and field service business 16 (16.8%); Developer 14 (14.7%)
- **visit_intent**: Has a specific problem to solve right now 50 (52.6%); Exploring ways to improve operations 45 (47.4%)
- **infobric_familiarity**: Has never heard of Infobric 49 (51.6%); Has heard the name but knows nothing more 35 (36.8%); Has seen Infobric equipment or the logo on a site 11 (11.6%)

## 3. Did they stay? Exit after the first screen vs the partner's analytics

- Left after the first screen (`left_early`): 0 of 95 = **0.0%**
- Would keep reading (`would_continue`): yes 95
- Partner ground truth for this page (90 days): Clarity Quick Backs **0.438** (10058 sessions), GA4 engaged share 0.884, avg engagement 11.1 s, scroll depth 0.352
- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); `left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.

| Visitor kind | n | left early | would continue = yes |
|---|---:|---:|---:|
| Supervisor or daily user | 28 | 0.0% | 100.0% |
| Finance or administration | 20 | 0.0% | 100.0% |
| Fleet, equipment or rental manager | 15 | 0.0% | 100.0% |
| Operations, project or site manager | 14 | 0.0% | 100.0% |
| Owner or senior manager | 13 | 0.0% | 100.0% |
| HSE or compliance | 5 | 0.0% | 100.0% |

## 4. The six partner dimensions (1-5) and the two follow-ups

| Dimension | n | mean | sd | 1 (1-5 share) | 2 (1-5 share) | 3 (1-5 share) | 4 (1-5 share) | 5 (1-5 share) | note |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| understanding | 95 | 4.01 | 0.10 | 0.0% | 0.0% | 0.0% | 98.9% | 1.1% | **collapsed** (sd < 0.3) |
| language_relevance | 95 | 4.01 | 0.10 | 0.0% | 0.0% | 0.0% | 98.9% | 1.1% | **collapsed** (sd < 0.3) |
| practical_value | 95 | 3.72 | 0.45 | 0.0% | 0.0% | 28.4% | 71.6% | 0.0% |  |
| trust | 95 | 3.00 | 0.00 | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | **collapsed** (sd < 0.3) |
| next_step_confidence | 95 | 3.85 | 0.35 | 0.0% | 0.0% | 14.7% | 85.3% | 0.0% |  |
| next_step_ease | 95 | 3.80 | 0.40 | 0.0% | 0.0% | 20.0% | 80.0% | 0.0% |  |
| cta_match | 95 | 4.67 | 0.47 | 0.0% | 0.0% | 0.0% | 32.6% | 67.4% |  |
| contact_likelihood | 95 | 2.82 | 0.66 | 0.0% | 32.6% | 52.6% | 14.7% | 0.0% |  |

### By visitor kind (mean)

| Visitor kind | n | understanding | language_relevance | practical_value | trust | next_step_confidence | next_step_ease | cta_match | contact_likelihood |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Supervisor or daily user | 28 | 4.04 | 4.00 | 3.68 | 3.00 | 3.89 | 3.86 | 4.79 | 2.71 |
| Finance or administration | 20 | 4.00 | 4.00 | 3.60 | 3.00 | 3.90 | 3.80 | 4.55 | 2.85 |
| Fleet, equipment or rental manager | 15 | 4.00 | 4.00 | 3.73 | 3.00 | 3.80 | 3.67 | 4.60 | 2.80 |
| Operations, project or site manager | 14 | 4.00 | 4.00 | 3.86 | 3.00 | 3.79 | 3.86 | 4.57 | 3.14 |
| Owner or senior manager | 13 | 4.00 | 4.08 | 3.85 | 3.00 | 3.77 | 3.77 | 4.69 | 2.77 |
| HSE or compliance | 5 | 4.00 | 4.00 | 3.60 | 3.00 | 4.00 | 3.80 | 5.00 | 2.60 |

## 5. What they would do next

- **Next step**: come_back_later 39 (41.1%); contact_sales 37 (38.9%); learn_more 19 (20.0%)
- **Needed before going further**: need_references_first 90 (94.7%); need_pilot_first 5 (5.3%)
- **Main basis of the decision**: fit 94 (98.9%); integrations 1 (1.1%)
- Converted (contact / demo / trial as the next step): 37 of 95 = 38.9%
- Information they missed most: price 95; integrations 95; setup_time 95; references 95; data_privacy 95; contract_terms 94; hardware 76
- Weakest part of the page: middle 52, top 22, bottom 21 · strongest: middle 53, top 42

| Visitor kind | come_back_later | contact_sales | learn_more |
|---|---:|---:|---:|
| Supervisor or daily user | 46.4% | 32.1% | 21.4% |
| Finance or administration | 25.0% | 55.0% | 20.0% |
| Fleet, equipment or rental manager | 73.3% | 20.0% | 6.7% |
| Operations, project or site manager | 21.4% | 57.1% | 21.4% |
| Owner or senior manager | 38.5% | 30.8% | 30.8% |
| HSE or compliance | 40.0% | 40.0% | 20.0% |

## 6. Quality gates for the case study

- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): 100.0% of 95
- Grounding: quoted claims found on the page 0.964, quoted phrases found on the page 0.969; trials with any ungrounded quote 40 of 95
- Primary button: inspected 100.0%, landed on the expected page 100.0%, label quoted correctly 100.0%

