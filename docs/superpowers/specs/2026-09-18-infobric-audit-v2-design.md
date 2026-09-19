# Infobric page audit v2 — design

Date: 2026-09-18, revised 2026-09-19 · Branch: `audit-v2` (from `real-partner`) · Status: all five pages built; report slimmed after the first smoke (§13)

## 1. Goal

Rebuild the Infobric page-audit task around the partner's pilot pack — the Main Brief,
five URL briefs and the 90-day GA4 / Clarity analytics — so that one run produces:

- **for the partner**: per page, an assessment on their six dimensions (1–5, defined
  anchors) by visitor kind, findings tied to exact wording with who they affect and how to
  check a fix, what to retain, and 3–5 priorities;
- **for the paper**: fields that are stable across arms, checkable against the page,
  comparable to the analytics, and separated into observations and judgments so the
  known rating-collapse (finding 1) can be measured rather than suffered.

Personas are out of scope (built separately: `persona/scripts/cohort_configs/PILOT_PERSONAS.md`).
The free-visit task is retired.

## 2. Pages and the persona contract

Five pages, one generated task each, from one master (`application/task-templates/web_infobric-audit-v2`):

| page_id | URL | eligible personas (`persona_strategy.json` filter) |
|---|---|---|
| `homepage` | https://infobric.com/se/ | all 1,500 |
| `fleet` | https://infobric.com/se/produkter/fleet/ | `deals_with_vehicles` = Part of my job |
| `driving_log` | https://infobric.com/se/produkter/fleet/elektronisk-korjournal/ | `deals_with_driving_logs` = Part of my job |
| `equipment` | https://infobric.com/se/produkter/equipment/ | `deals_with_tools_equipment` = Part of my job |
| `hyrma` | https://infobric.com/se/produkter/hyrma/ | `works_in_rental_process` = Part of my job |

Every task stratifies by `audience_group` (the partner's six visitor kinds). Personas
carry their own situation (`job_role`, `visit_intent`, `infobric_familiarity`,
`vehicle_pain_point`, `tool_tracking_today`, `rental_side`, `device_context`, …), so the
task ships **no scenario text**. `input/context.md` holds only the page's purpose in
neutral words. No analytics number reaches the persona.

Fields the task reads from the persona file (`/app/input/persona.yaml`) for fidelity
checks: `visit_intent`, `audience_group`, `tier`, `device_context`.

## 3. The visit, in order

1. **Self-briefing** (before opening the page): 2–3 sentences — who I am, what I deal
   with day to day that matters here, why I am looking today, what I already know of
   Infobric. Pulls the persona's fields next to the judgments; checkable against the
   persona file.
2. **First screen** (before scrolling): what the visitor thinks this is, whether it matches
   what they expected, whether they would continue.
3. **Full page**: the partner's nine questions as observations with quoted wording and a
   position (top / middle / bottom), plus the six dimension scores.
4. **One CTA click**: the page's primary next-step button, clicked once; what follows is
   described and compared with the expectation the button set. Nothing is submitted.
   Anything not inspected is `unknown`.
5. **Decision** and save.

No other navigation. The page is assessed as a standalone entry point (Main Brief §3).

## 4. Artifact: `/app/output/page_audit.json`

O = observation (checkable against the page or the persona), J = judgment.

| Block | Field | Kind | Values |
|---|---|---|---|
| A | `self_briefing` | O/persona | text |
| A | `arrived_with` | O/persona | `specific_problem` · `exploring` |
| B | `first_screen_takeaway` | O | text |
| B | `first_screen_expectation_match` | J | 1–5 |
| B | `would_continue` | J | `yes` · `no` |
| B | `would_continue_reason` | O | text |
| C | `what_it_does` | O | text, own words |
| C | `problems_recognised` | O | list of text |
| C | `language_felt_familiar` | O | list of quoted phrases |
| C | `language_felt_off` | O | list of quoted phrases |
| C | `claims_credible` | O | list of quoted claims |
| C | `claims_need_proof` | O | list of quoted claims |
| C | `confusing_or_missing` | O | list of `{what, where, kind}`; kind ∈ confusing · missing · unconvincing · irrelevant |
| C | `dead_click_candidates` | O | list of text |
| C | `attention_stop_point` | J | `top` · `middle` · `bottom` · `read_all` |
| C | `strongest_element`, `strongest_position` | O | text; top · middle · bottom |
| C | `weakest_element`, `weakest_position` | O | text; top · middle · bottom |
| C | `hesitate_or_leave_reason` | O | text |
| C | `understanding`, `language_relevance`, `practical_value`, `trust`, `next_step_confidence` | J | 1–5 |
| C | `next_step_ease` | J | 1–5 or `unknown` (unknown unless the CTA was inspected) |
| D | `primary_cta_seen` | O | exact button label |
| D | `cta_expectation` | J | text |
| D | `cta_inspected` | O | true · false |
| D | `cta_page_url` | O | URL or `unknown` |
| D | `cta_reality` | O | text or `unknown` |
| D | `form_asks_for` | O | list of text (empty if none) |
| D | `cta_match` | J | 1–5 or `unknown` |
| E | `next_step` | J | page-specific subset of: `book_demo` `start_trial` `create_free_account` `order_package` `use_calculator` `download_guide` `preview_fleet` `contact_sales` `learn_more` `come_back_later` `leave` |
| E | `basis_primary` | J | `legal_compliance` `consolidation` `price` `integrations` `ease_of_rollout` `proof_references` `support` `features` `fit` `other` |
| E | `trust_action` | J | `share_data_now` `need_references_first` `need_pilot_first` `would_not_proceed` |
| E | `contact_likelihood` | J | 1–5 |
| E | `missing_info` | O | subset of `price` `integrations` `hardware` `setup_time` `references` `data_privacy` `contract_terms` |
| E | `reason` | O/J | text |
| E | `improvement_suggestion`, `improvement_check` | J | text; how to tell whether it helped |
| E | `retain` | O | text — what works and should be kept |

Six-dimension anchors (in the instruction and the report legend):

- **understanding** 1 = still could not say what they sell · 3 = know the category, not what it would do for me · 5 = could explain to a colleague what it does and for whom
- **language_relevance** 1 = written for someone else · 3 = general business language, some familiar examples · 5 = my situations and words; I recognised my own problems
- **practical_value** 1 = no idea what would change day to day · 3 = plausible benefit, not concrete · 5 = I can name what gets easier or cheaper for me
- **trust** 1 = would not share my data with them · 3 = credible company, claims unproven for my case · 5 = would put my own operation on it without asking for references
- **next_step_confidence** 1 = no idea what to do next or what would happen · 3 = I see a button but not what follows · 5 = I know exactly what happens after clicking and it suits me
- **next_step_ease** 1 = unclear, demanding or off-putting · 3 = doable with friction · 5 = quick and obvious · `unknown` if not inspected

## 5. Ground truth per page: `input/inventory.json`

Hand-checked, dated, drafted by `application/scripts/build_inventory.py` (stdlib fetch +
parse) and confirmed by a person:

```
page_id, url, checked, truth_statement,
primary_cta {label, url_fragment}, secondary_ctas [{label, url_fragment}],
available_next_steps [...], conversion_next_steps [...], navigation_next_steps [...],
claims [exact strings], sections [{name, position}], trust_signals_present [...],
shows_price, text_snapshot (visible text)
```

The verifier uses it to emit **grounding facets**: share of quoted claims/phrases found
in the snapshot, whether `primary_cta_seen` is a real CTA label, whether `cta_page_url`
reached the CTA target. The oracle uses it to click the right button.

## 6. Verifier contexts and facets

Validity gate (schema, enums, page-specific `next_step`) plus facets:

| context | contextType | facets |
|---|---|---|
| `decision.primary` | decision | `decision_outcome`, `basis_primary`, `reason`, `decision_subject_label`, `decision_subject_id`, `converted` (per page's conversion set), `contact_likelihood`, `trust_action` |
| `first_impression.primary` | first_impression | `first_screen_expectation_match`, `would_continue`, `first_screen_takeaway`, `would_continue_reason` |
| `page_audit.<page>` | page_audit | the six dimensions, `attention_stop_point`, `claims_grounded_share`, `phrases_grounded_share`, `ungrounded_quotes`, `dead_click_count`, `confusing_or_missing_count`, `missing_info`, `what_it_does`, `unmapped_values`, `json_health`, `instrument_version`, `variant`, `device_reviewed` |
| `cta_followthrough.primary` | cta_followthrough | `cta_inspected`, `cta_label_grounded`, `cta_url_ok`, `cta_match`, `cta_expectation`, `cta_reality`, `form_asks_for` |
| `page_improvement.<page>` | page_improvement | `improvement_suggestion`, `improvement_check`, `retain`, `strongest_element` (+position), `weakest_element` (+position), `hesitate_or_leave_reason`, `problems_recognised`, `claims_need_proof`, `language_felt_off` |
| `persona_fidelity.primary` | persona_fidelity | `self_briefing`, `arrived_with`, `arrived_with_matches_persona` |
| `task_outcome.primary` | task_outcome | standard |

The verifier is deterministic: no model calls. Paths come from env (`AUDIT_OUTPUT`,
`AUDIT_INPUT_DIR`) so it can be unit-tested on the host.

## 7. Scores: in-browse and post-hoc

The six dimensions, `first_screen_expectation_match`, `cta_match` and `contact_likelihood`
are collected in-browse. `application/scripts/score_audit.py` (built after the homepage
smoke) re-derives them from persona + self-briefing + the O fields and writes `*_scored`
facets back into each trial's `structured_output.json`. The partner report uses the scored
values; the paper reports both and the delta. If the Playground report does not pick up
the added facets, the partner overview is produced by a report script from the scored
aggregation.

## 8. Report structure (the partner deliverable, per page)

| Report section (Main Brief §7) | Fed by |
|---|---|
| Compact overview: six dimensions by visitor kind, anchor legend, "cannot be assessed" | page_audit + cta_followthrough (scored) |
| Findings: exact wording, who it affects, what it creates, proposed improvement, how to check | first_impression, page_audit grounding, page_improvement, cta_followthrough |
| Audience differences preserved (incl. "values it but not ready") | every context by `audience_group`; `trust_action` + `next_step` = learn_more with high value |
| Priorities (3–5) and what to retain | page_improvement summaries |
| Three-layer labels: visible on site / supported by analytics / persona interpretation | O fields (grounded) / `ablation/ground_truth/analytics_90d.json` / J fields |

`reporting.json` groups by `audience_group`, then `tier`, `visit_intent`,
`infobric_familiarity`, `device_context`. LLM summaries are instructed to label quoted
wording separately from interpretation; the analytics layer is added by the report.

## 9. Ablation hooks

- `instrument_version` and `variant` facets on every trial.
- `skim` variant (first screen only, decide in seconds) generated for every page via
  `input/variant.txt`; built, not run.
- Persona-set arms (pilot-full / generic / label) are dataset swaps; `persona_fidelity`
  measures whether the persona is read.
- In-browse vs post-hoc scores on the same trials (finding 1 replication).
- `journey.py` (generalised) verifies the CTA click from the trajectory.
- Analytics baseline for calibration: pages/session, Quick Backs, scroll depth, conversion
  rate per page.

## 10. Mechanics

- Agent: `persona-browser-use`; save via `write_file`; never-end and blank-page lines;
  no Python/shell.
- Desktop only; `device_reviewed = desktop`; mobile marked not assessed.
- `make_audit_v2_tasks.py` generates the five tasks (+ skim variants) from the master;
  registry entries `web_infobric-audit-v2-<page>`.
- Retire `web_infobric-free-visit` (task dir, registry entry, README §6.6 references).
- v1 page-audit tasks stay until v2 is validated on all five pages, then are retired.

## 11. Build order and tests

1. Homepage: master + brief + inventory + verifier + oracle + reporting + generator +
   registry. Oracle run (verifier validity), then a 6-persona UI smoke (one per visitor
   kind), reviewed with the partner deliverable in mind before pages 2–5.
2. Pages 2–5: briefs + inventories; probes of 4–6 personas each.
3. `score_audit.py`, `analytics_90d.json`, retirement of free-visit.
4. Host-side verifier unit tests; registry test for the five ids.

Sizing for the pilot (later decision): ~150 homepage, ~100 per product page, every
eligible visitor kind ≥ 30; ≈ 550 trials, ≈ 6–7 h at concurrency 3.

## 12. Known limits

Mobile not simulated. Form submission, confirmation and follow-up are never exercised
(`unknown`). Personas are first-time visitors; Hyrma's real traffic is 61% returning, so
its analytics are not a clean baseline. Ratings collected in-browse are expected to be
compressed; the scored values are the reported ones.

## 13. Revision after the first smoke (2026-09-19)

The first six-trial report was overwhelming: 70 facets per trial, 550 persona-insight
cards and a second questionnaire on a 1–10 scale. Four changes, all implemented:

1. **One questionnaire, one scale.** `input/self_report_schema.yaml` (a generic post-run
   form on 1–10, inherited from the v1 task) is removed; the Playground skips the step
   when the file is absent. Everything is 1–5.
2. **Two output files.** `structured_output.json` carries only what maps to a section
   of the partner's brief (six dimensions, `would_continue`, `cta_match`, `next_step`,
   `trust_action`, `contact_likelihood`, the contract facets, and four composite texts
   — `takeaway_text`, `findings_text`, `cta_text`, `changes_text` — that the four report
   summaries are written from). `quality.json` carries the ablation layer: grounding,
   CTA checks, persona fidelity, instrument version, variant, JSON health, raw scores.
   The report never reads it. Result on the same six trials: 63 → 24 facets, 37 → 15
   chartable.
3. **Questionnaire cuts.** `dead_click_candidates` (the agent cannot experience dead
   clicks), `attention_stop_point` (uniform; the skim variant is the honest signal),
   `first_screen_expectation_match` (redundant with `would_continue` + reason). 
   `arrived_with` stays in the questionnaire as a fidelity check but is no longer a
   report facet (the persona's own `visit_intent` gives that cut).
4. **Playground: `personaDimensions` allow-list in `reporting.json`.** Persona insights
   crosses only the listed dimensions (`audience_group`, `tier`, `visit_intent`,
   `infobric_familiarity`); cards are pinned to `audience_group`. Backwards-compatible:
   tasks that do not declare it are unchanged. On the same six trials: 550 → 11 cards,
   47,644 → 84 explorer options.

Paired re-probe after the self-briefing edit: persona fidelity 5/5 (was 3/6).
