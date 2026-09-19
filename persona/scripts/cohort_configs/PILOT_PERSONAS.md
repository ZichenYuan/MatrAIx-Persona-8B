# Infobric pilot persona sets — pilot-full, pilot-generic, pilot-label

Persona pools for the Infobric website pilot, designed from the partner's pilot pack:
the Main Brief, the five URL briefs, and the 90-day GA4 and Microsoft Clarity analytics.

The plan is one master set of people plus two sets made by **hiding parts of those same
people**. Think of each persona as a full CV. `pilot-full` is the full CV. The other two
are the same CVs with sections blacked out. Because persona 0042 is the same person in
every set, results can be compared person by person. The older v0 / v1 / v2 sets
(see `README.md` in this folder) cannot do that: v1 and v2 are different people.

| Set | Status | Pool directory (`persona/datasets/`) | What the model sees |
|---|---|---|---|
| **pilot-full** | **built 2026-09-18** | `generated-persona-dev-infobric-pilot-full` | Everything: label, study fields, generic schema (1,323 to 1,327 fields) |
| **pilot-generic** | TODO | `generated-persona-dev-infobric-pilot-generic` | Same people, study fields hidden: label + generic schema |
| **pilot-label** | TODO | `generated-persona-dev-infobric-pilot-label` | Same people, name + company type + job role only |

Pool directories are gitignored (`persona/datasets/generated-persona-dev-*/`). Rebuild them
with the commands in the last section. The pool holds `manifest.json`, one
`persona_NNNN.yaml` per person, `validation.md` (target vs built shares per sampling group)
and `audit.md` (the tables below, from `persona/scripts/audit_pilot_cohort.py`).

The older sets stay frozen under their own names. Past runs point at their persona ids.

---

## Why a new pool

The partner's briefs describe a wider audience than v0 / v1 / v2 contain.

| The briefs ask for | v2 had | pilot-full has |
|---|---|---|
| Five pages: homepage, Fleet, Electronic Driving Log, Equipment, Hyrma | one pool, no page marker | a page audience field per product page |
| Supervisors, drivers, tool users, payroll and finance staff, rental administrators | managers only | 43 % staff, 57 % managers |
| Finance, procurement, service, transport and rental-sales jobs | 6 roles | 17 roles |
| Any Swedish business with vehicles (Fleet, Driving Log) | construction only | a fifth company type outside construction |
| "Some arrive with a specific problem, others are exploring" | not modelled | `visit_intent` |
| "May know little or nothing about Infobric" | not modelled | `infobric_familiarity` (nobody is a customer) |
| Desktop and mobile review | not controlled | `device_context` limited to those two |
| The person's real situation per product | one field (digital tools) | vehicles, driving logs, tools, rental fields |

---

## pilot-full

Config: `persona/scripts/cohort_configs/infobric_pilot_full.yaml`. Built by
`persona/scripts/build_cohort.py` with the pin-early / filter-late recipe (PLAN.md §4):
pin fields the sampler draws early (age, domain, income, gender) as exact cells, and
filter fields it draws late (seniority, industry experience).

### Three layers per persona

| Layer | What it holds | Kept in |
|---|---|---|
| A. Label | Display name, company type (`tier`), `job_role` | all three sets |
| B. Study fields | 38 fields written for this study (34 for non-rental companies): Swedish title, responsibilities, product situations, reason for visit, page audiences | pilot-full only |
| C. Generic schema | The 1,289 general fields: age, personality, skills, attitudes | pilot-full and pilot-generic |

### Four sampling groups (1,500 people)

Managers and staff need different seniority filters, so the builder draws them as separate
groups. All four share: Swedish native (language and culture), Western Europe, works at a
company (no academia, NGO or public sector), practitioner stance, some English.

| Group | People | Seniority | Industry experience required |
|---|---:|---|---|
| construction-managers | 690 | Manager, Director, VP, C-suite, Founder; 6+ years | construction: Veteran or Experienced |
| construction-staff | 510 | Entry, Mid, Senior, Lead / Principal | construction: Veteran or Experienced |
| fieldservice-managers | 165 | as managers above | transportation: Veteran or Experienced |
| fieldservice-staff | 135 | as staff above | transportation: Veteran or Experienced |

**Cells (exact head counts per group):** age × domain × household income × gender.

- **Age** uses the split required by the study brief, 17 / 31 / 26 / 20 / 6 % for 25-34 up
  to 65-74, in every group. The whole pool therefore matches it (table below).
- **Domain** decides the role family. Engineering or Skilled Trades gives operational
  managers and field staff. Business & Management or Finance & Economics gives business
  managers and office staff. A payroll clerk never comes from a trades background.
- **Gender** depends on domain (assumed): Skilled Trades 88 / 12 for managers and 92 / 8
  for staff; Finance & Economics 50 / 50 for managers and 30 / 70 for staff.
- **Income:** managers 50 / 40 / 10 % over $50k-100k, $100k-200k, $200k+; construction
  staff 25 / 60 / 15 % over $25k-50k, $50k-100k, $100k-200k.

### Company types (`tier`)

| Company type | People | `company_business` examples |
|---|---:|---|
| Main contractor | 312 | General building contractor, civil works contractor |
| Subcontractor | 312 | Electrical, plumbing and ventilation, groundworks, carpentry, painting, scaffolding |
| Developer | 204 | Housing developer, commercial property owner, municipal housing company |
| Rental | 372 | Machine rental, tool rental, lifts / scaffolding / site cabins |
| Vehicle and field service business | 300 | Transport and haulage, installation and service, machine contractor, property maintenance |

Rental is the largest construction type on purpose. It is the only source of people for
the Hyrma page, whose brief lists six visitor kinds.

**Existing tasks:** `web_infobric-page-audit` and `web_infobric-free-visit` ship a
`context.md` with four tier situations, and the tier-page verifier knows four tiers. A
"Vehicle and field service business" persona has no matching situation there. Filter
`tier` to the four construction types for those tasks until the five product-page tasks,
with their own situations, exist.

### Job roles (`job_role`), drawn from company type and role family

| Role | People | Swedish titles (`job_title_sv`) | Partner's visitor kind (`audience_group`) |
|---|---:|---|---|
| Executive or owner | 191 | VD, Ägare, Regionchef | Owner or senior manager |
| Site or project manager | 121 | Platschef, Projektchef, Arbetschef, Projektledare | Operations, project or site manager |
| Operations manager | 82 | Driftchef, Produktionschef, Verksamhetschef | Operations, project or site manager |
| HSEQ manager | 47 | KMA-chef, HSEQ-ansvarig, Arbetsmiljöchef | HSE or compliance |
| Fleet or vehicle manager | 63 | Fordonsansvarig, Fordonschef, Transportchef | Fleet, equipment or rental manager |
| Machine or equipment manager | 31 | Maskinchef, Maskinansvarig | Fleet, equipment or rental manager |
| Tool or asset manager | 24 | Verktygsansvarig, Förrådsansvarig, Logistikansvarig | Fleet, equipment or rental manager |
| Rental or depot manager | 66 | Depåchef, Uthyrningschef, Filialchef | Fleet, equipment or rental manager |
| Service or maintenance manager | 44 | Verkstadschef, Serviceansvarig, Servicechef | Fleet, equipment or rental manager |
| Finance or administration manager | 129 | Ekonomichef, Administrativ chef, Controller | Finance or administration |
| Procurement manager | 57 | Inköpschef, Inköpsansvarig | Finance or administration |
| Supervisor or foreman | 131 | Arbetsledare, Lagbas, Verkstadsförman | Supervisor or daily user |
| HSE or compliance coordinator | 32 | KMA-samordnare, Arbetsmiljösamordnare, Skyddsombud | HSE or compliance |
| Finance or payroll staff | 166 | Löneadministratör, Ekonomiassistent, Administratör | Finance or administration |
| Rental sales or administrator | 41 | Uthyrare, Innesäljare, Kundtjänstmedarbetare | Finance or administration |
| Transport or logistics coordinator | 96 | Transportledare, Logistiksamordnare, Transportplanerare | Supervisor or daily user |
| Driver or field worker | 179 | Yrkesarbetare, Servicetekniker, Chaufför, Maskinförare | Supervisor or daily user |

`audience_group` is the partner's own list of six visitor kinds (Main Brief §4). Use it to
group results in reports.

### Study fields (layer B)

Everything downstream of `job_role` is drawn conditional on it, so a persona's duties form
one coherent package. Stamped fields are assigned with exact quotas in a seeded random
order, so two stamped fields are independent of each other.

| Field | Values | Drawn conditional on |
|---|---|---|
| `tier` | five company types | sampling group |
| `company_business` | 18 kinds of company | `tier` |
| `work_country`, `sweden_region` | Sweden; six regions (Stockholm 30 … Norrland 10) | — |
| `job_role`, `job_title_sv`, `work_setting` | see above; settings include Workshop, On the road, Rental branch | `tier` + role family; `job_role` |
| `resp_project_delivery`, `resp_safety_hseq`, `resp_vehicles_fleet`, `resp_heavy_equipment`, `resp_tools_assets`, `resp_rental_operations`, `resp_finance_admin` | Owns, Shares, Not involved | `job_role` |
| `crew_size_managed` | No direct reports, 1-10, 11-50, 51-200, 200+ | `job_role` |
| `purchasing_authority` | No say, Gives input as a user, Recommends, Approves within budget, Final decision | `job_role` |
| `digital_tools_today` | Paper and phone calls … Integrated platform | `tech_savviness` |
| `company_vehicles` | 1-5, 6-20, 21-100, 100+ | `company_size` |
| `vehicle_use` | Service vans and pickups, Company cars with private use, Pool cars shared by staff, Trucks and heavy vehicles, Mixed fleet | `tier` |
| `driving_log_today` | Paper logbook, From memory at month end, Spreadsheet, Electronic log already, None kept | `tech_savviness` |
| `vehicle_pain_point` | eight headaches taken from the Fleet and Driving Log briefs | `job_role` |
| `tracking_privacy_concern` | Low, Some, High | `job_role` (drivers highest) |
| `payroll_accounting_system` | Fortnox, Visma, Hogia, Large ERP, Other or not sure | `company_size` |
| `tool_tracking_today` | Nothing formal, Paper lists, Spreadsheet, Dedicated system | `tech_savviness` |
| `tool_inventory_size` | Under 100, 100-1000, Over 1000 items | `company_size` |
| `equipment_pain_point` | six headaches taken from the Equipment brief | `job_role` |
| `rental_side` | Rents out to customers; or rents in every week / every month / rarely | `tier` |
| `rental_system_today`, `rental_depots`, `rental_fleet_size`, `rental_pain_point` | **Rental companies only**; absent for everyone else. Fleet size follows depot count. | `tier`; `rental_depots` |
| `visit_intent` | Has a specific problem to solve right now 50 / Exploring ways to improve operations 50 | — |
| `infobric_familiarity` | Never heard of Infobric 55 / Heard the name 30 / Seen the logo on a site 15 | — |
| `audience_group` | the partner's six visitor kinds | rule on `job_role` |
| four page-audience fields | Part of my job / Not part of my job | rules, next section |

**Role-linked repairs** keep the generic schema consistent with the stamped role: the job
function fits the role (finance roles are Finance, executives are Executive), executives
are at least Director, supervisors are not Entry level, drivers drive daily, finance
roles know accounting, HSEQ roles know quality assurance, and so on. Generic clean-up:
generation fits the age bracket, a Swedish native is not a visa holder, the income band
fits the household income, and subject specialty fits the domain.

### Which personas go with which page

The page audiences are written as **facts about the job, never as page names**. The brief
says these visitors know little or nothing about Infobric, and every field is shown to the
model as a line of text. A field called "eligible for the Hyrma page" would leak that.

Use these filters in a task's `persona_strategy.json` (`dimensionFilters`):

| Page | Filter | Eligible |
|---|---|---:|
| 1. Homepage | none | 1,500 |
| 2. Infobric Fleet | `deals_with_vehicles` = Part of my job | 1,071 |
| 3. Electronic Driving Log | `deals_with_driving_logs` = Part of my job | 900 |
| 4. Infobric Equipment | `deals_with_tools_equipment` = Part of my job | 1,055 |
| 5. Infobric Hyrma | `works_in_rental_process` = Part of my job | 289 |

Rules: a role named in the page's brief, or owning the matching responsibility. Driving
logs also need cars, vans or pool cars (heavy trucks are excluded). Hyrma needs a Rental
company and one of the roles its brief lists.

### Audit (2026-09-18) — page coverage

Every visitor kind named in a URL brief, with the roles that stand for it. "Thin" means
fewer than 30 people. **No cell is thin.**

| Page | Visitor kind in the brief | People |
|---|---|---:|
| Homepage | Owners or senior managers | 191 |
| Homepage | Operations, project or site managers | 203 |
| Homepage | Fleet, equipment or rental managers | 228 |
| Homepage | Finance or administration staff | 393 |
| Homepage | HSE or compliance staff | 79 |
| Homepage | Supervisors and daily users | 406 |
| Fleet | Fleet or vehicle managers | 159 |
| Fleet | Operations or administration managers | 211 |
| Fleet | Finance, payroll or accounting staff | 166 |
| Fleet | Owners and senior managers | 191 |
| Fleet | Supervisors and drivers | 310 |
| Driving Log | Fleet or vehicle managers | 135 |
| Driving Log | Finance, payroll or administration staff | 251 |
| Driving Log | Owners and operations managers | 220 |
| Driving Log | Supervisors responsible for drivers | 111 |
| Driving Log | Drivers | 157 |
| Equipment | Equipment or tool managers | 55 |
| Equipment | Operations, project or site managers | 203 |
| Equipment | Owners and senior managers | 191 |
| Equipment | Procurement or finance staff | 186 |
| Equipment | Supervisors and tool users | 310 |
| Hyrma | Owners and managing directors | 46 |
| Hyrma | Rental or operations managers | 80 |
| Hyrma | Sales and rental administrators | 41 |
| Hyrma | Service and maintenance managers | 35 |
| Hyrma | Transport or logistics coordinators | 38 |
| Hyrma | Finance and administration staff | 49 |

### Audit — age requirement

| Age | Required % | Whole pool % | Managers % | Staff % | People |
|---|---:|---:|---:|---:|---:|
| 25-34 | 17 | 17.1 | 17.1 | 17.2 | 257 |
| 35-44 | 31 | 31.1 | 31.1 | 31.0 | 466 |
| 45-54 | 26 | 26.1 | 26.1 | 26.2 | 392 |
| 55-64 | 20 | 19.8 | 19.9 | 19.7 | 297 |
| 65-74 | 6 | 5.9 | 5.8 | 5.9 | 88 |

Largest gap: 0.2 percentage points (3 people of 1,500). It comes from rounding head counts
over about 120 small cells per group. No persona falls outside the five brackets.

### Audit — coherence (all 0 of 1,500)

Swedish language and culture Native · work country Sweden · role, title and company type
present · no staff role with manager seniority and no manager role with staff seniority ·
finance roles have a Finance (or, for payroll staff, HR) job function · executives have
the Executive function · no trades background in a finance role · generation fits age ·
no Swedish native marked visa holder · rental fields only on rental companies and on all
of them · the Hyrma audience is inside rental companies only · drivers drive daily ·
device is desktop or mobile · everyone works at a company · no build helper field leaked ·
no duplicate display names.

The build filled every cell from its own draws (0 people borrowed from another cell) in
14 minutes.

### Key distributions

Gender 72 / 28 (women: payroll staff 67 %, procurement 44 %, finance managers 43 %,
supervisors 10 %, drivers 12 %) · company size 41 % SMB, 20 % Startup, 18 % Mid, 17 %
Enterprise, 4 % Solo · device 54 % mobile, 46 % desktop · seniority 30 % Manager, 17 %
Director, 7 % Founder, 4 % VP or C-suite, 43 % staff levels.

### Known limits

- **Same age split in every group.** It guarantees the overall requirement and keeps age
  from being tangled with role, but it is unrealistic at the edges: 30 of 191 executives
  are aged 25-34 (7 of them at a mid-size or large company), and 25 of 386 drivers,
  payroll and rental staff are aged 65-74. The alternative is to tilt staff younger and
  managers older so the two still average to the required split, and to make the builder
  fix the age head counts first so the overall match is exact. Not done yet; decision open.
- **The job role is stamped without looking at age or company size.** The generic fields
  the sampler draws (seniority, years of experience) do follow age.
- **Finance or administration is the largest visitor kind (26 %).** It follows from the
  domain shares, not from any traffic data. Change the domain shares to rebalance.
- **Vehicle businesses are sampled through transportation experience only.** An
  installation-and-service company persona therefore also has a transport background.
- **Nobody is an existing customer.** The analytics show many returning users and logins
  on the homepage (43 % returning) and on Hyrma (61 % returning, 12,576 login events).
  The brief asks for people who know little about Infobric, so the pool models first-time
  visitors only. Reports should say so when comparing with the analytics.
- **Mobile cannot be simulated yet.** `device_context` records the split, but the browser
  agent has no mobile viewport setting.

### What the analytics did and did not change

GA4 and Clarity describe page behaviour, not who the visitors are. They gave no reason to
change age, region or company-type shares. They did shape two decisions: personas are
first-time visitors (above), and Hyrma gets a deep audience because its real traffic is
mixed with logins and cannot serve as a clean baseline.

### Assumptions to confirm with the partner

Swedish job titles for the eleven new roles · role shares per company type · the share of
staff versus managers (43 / 57) · company-type shares (Rental 25 %, Developer 14 %) · the
fifth company type and its four business kinds · gender split by domain · income bands ·
region shares · the 50 / 50 split of `visit_intent` and the 55 / 30 / 15 split of
`infobric_familiarity` · which roles count as the audience of each page (the rules above).

---

## pilot-generic — TODO

Same 1,500 people, same ids, with layer B (the 38 study fields) hidden. Tests whether the
explicit study fields matter, with the people held constant. Needed before it can be built:

1. `strip_cohort.py` only has `--keep`. Add `--drop` (remove the listed fields, keep the rest).
2. The role-linked repairs raise generic fields (a finance manager becomes Proficient in
   accounting), which leaks role information into layer C. Have the builder record the
   original values so this set can show them untouched.
3. Decide whether `tier` and `job_role` stay (they are the label, layer A). Proposed: yes.

## pilot-label — TODO

Same 1,500 people, same ids, display name + `tier` + `job_role` only. The floor: if this
set gives the same answers as pilot-full, the model is not reading the persona. Can be
built today with `strip_cohort.py --keep tier job_role`; left until pilot-generic is
ready so the three are made from one frozen pilot-full.

A possible fourth set, **pilot-study** (layers A + B, about 40 fields, no generic schema),
would test whether the 1,289 generic fields add anything. The trust-rating finding
(`ablation/findings/trust-rating-collapse.md`) suggests a 25,000-character persona gets
drowned out during a long browse, so this may be the most informative arm.

---

## How to use pilot-full

Pick the page, apply its filter, stratify by the partner's visitor kinds:

```json
{
  "pool": "persona/datasets/generated-persona-dev-infobric-pilot-full",
  "dimensionFilters": { "works_in_rental_process": ["Part of my job"] },
  "sampling": { "mode": "stratified", "fields": ["audience_group"], "allocation": "proportional" }
}
```

In the Playground: Dataset → "Infobric pilot — full", then Persona filters → the page's
field. Switch "Task default persona strategy" off only after checking the dataset, because
that switch resets the dataset and clears filters.

## Rebuild

```bash
uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_pilot_full.yaml   # ~14 min
uv run python persona/scripts/audit_pilot_cohort.py persona/datasets/generated-persona-dev-infobric-pilot-full \
  --out persona/datasets/generated-persona-dev-infobric-pilot-full/audit.md
# quick trial of a config change (2 to 4 min):
uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_pilot_full.yaml \
  --total 120 --out persona/datasets/generated-persona-dev-infobric-pilot-trial
```

The build is seeded (`seed: 42`), but treat a rebuild as a new draw: any config change
moves persona ids. **Freeze pilot-full before building the other two sets from it**, and
keep a copy outside the repo, because the pool folder is gitignored.
