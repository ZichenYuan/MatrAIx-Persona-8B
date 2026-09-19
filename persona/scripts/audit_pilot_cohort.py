#!/usr/bin/env python3
"""Audit an Infobric pilot pool against the partner's five URL briefs.

    uv run python persona/scripts/audit_pilot_cohort.py persona/datasets/generated-persona-dev-infobric-pilot-full
    uv run python persona/scripts/audit_pilot_cohort.py <pool> --out <pool>/audit.md --min 30

Three questions, in order of importance:
1. Page coverage — does every page have enough of each visitor kind its brief lists?
2. Coherence — do the stamped role, the sampled background and the product fields agree?
3. Shape — who is in the pool (company type, role, age, gender, device, visit reason)?

`PAGES` below is the single place that says which personas belong to which page. Use the
same filters in a task's persona_strategy.json.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

YES = "Part of my job"
MANAGER_SENIORITY = {"Manager", "Director", "VP", "C-suite", "Founder"}
STAFF_ROLES = {"HSE or compliance coordinator", "Finance or payroll staff", "Rental sales or administrator",
               "Transport or logistics coordinator", "Driver or field worker", "Supervisor or foreman"}
FINANCE_ROLES = {"Finance or administration manager", "Finance or payroll staff"}
RENTAL_FIELDS = ("rental_system_today", "rental_depots", "rental_fleet_size", "rental_pain_point")
AGE_REQUIRED = {"25-34": 17, "35-44": 31, "45-54": 26, "55-64": 20, "65-74": 6}  # study brief
GENERATION = {"18-24": {"Gen Z"}, "25-34": {"Gen Z", "Millennial"}, "35-44": {"Millennial"},
              "45-54": {"Gen X"}, "55-64": {"Gen X", "Boomer"}, "65-74": {"Boomer"}}

# page -> (url, persona filter, {visitor kind named in the URL brief: job roles that stand for it})
PAGES = {
    "1. Homepage": ("https://infobric.com/se/", {}, {
        "Owners or senior managers": ["Executive or owner"],
        "Operations, project or site managers": ["Site or project manager", "Operations manager"],
        "Fleet, equipment or rental managers": ["Fleet or vehicle manager", "Machine or equipment manager", "Tool or asset manager",
                                                "Rental or depot manager", "Service or maintenance manager"],
        "Finance or administration staff": ["Finance or administration manager", "Finance or payroll staff", "Procurement manager",
                                            "Rental sales or administrator"],
        "HSE or compliance staff": ["HSEQ manager", "HSE or compliance coordinator"],
        "Supervisors and daily users": ["Supervisor or foreman", "Driver or field worker", "Transport or logistics coordinator"],
    }),
    "2. Infobric Fleet": ("https://infobric.com/se/produkter/fleet/", {"deals_with_vehicles": YES}, {
        "Fleet or vehicle managers": ["Fleet or vehicle manager", "Transport or logistics coordinator"],
        "Operations or administration managers": ["Operations manager", "Finance or administration manager"],
        "Finance, payroll or accounting staff": ["Finance or payroll staff"],
        "Owners and senior managers": ["Executive or owner"],
        "Supervisors and drivers": ["Supervisor or foreman", "Driver or field worker"],
    }),
    "3. Electronic Driving Log": ("https://infobric.com/se/produkter/fleet/elektronisk-korjournal/", {"deals_with_driving_logs": YES}, {
        "Fleet or vehicle managers": ["Fleet or vehicle manager", "Transport or logistics coordinator"],
        "Finance, payroll or administration staff": ["Finance or payroll staff", "Finance or administration manager"],
        "Owners and operations managers": ["Executive or owner", "Operations manager"],
        "Supervisors responsible for drivers": ["Supervisor or foreman"],
        "Drivers": ["Driver or field worker"],
    }),
    "4. Infobric Equipment": ("https://infobric.com/se/produkter/equipment/", {"deals_with_tools_equipment": YES}, {
        "Equipment or tool managers": ["Tool or asset manager", "Machine or equipment manager"],
        "Operations, project or site managers": ["Operations manager", "Site or project manager"],
        "Owners and senior managers": ["Executive or owner"],
        "Procurement or finance staff": ["Procurement manager", "Finance or administration manager"],
        "Supervisors and tool users": ["Supervisor or foreman", "Driver or field worker"],
    }),
    "5. Infobric Hyrma": ("https://infobric.com/se/produkter/hyrma/", {"works_in_rental_process": YES}, {
        "Owners and managing directors": ["Executive or owner"],
        "Rental or operations managers": ["Rental or depot manager", "Operations manager"],
        "Sales and rental administrators": ["Rental sales or administrator"],
        "Service and maintenance managers": ["Service or maintenance manager"],
        "Transport or logistics coordinators": ["Transport or logistics coordinator"],
        "Finance and administration staff": ["Finance or administration manager", "Finance or payroll staff"],
    }),
}


def table(title: str, rows: list[dict], key: str, top: int | None = None) -> list[str]:
    c = Counter(r.get(key, "—") for r in rows)
    items = c.most_common(top) if top else sorted(c.items(), key=lambda kv: -kv[1])
    out = [f"**{title}** (n={len(rows)})", "", "| value | n | % |", "|---|---:|---:|"]
    out += [f"| {k} | {v} | {100 * v / max(len(rows), 1):.1f} |" for k, v in items]
    return out + [""]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pool", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--min", type=int, default=30, help="flag a page x visitor kind below this count (default 30)")
    args = ap.parse_args()

    rows = []
    for f in sorted(args.pool.glob("persona_*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        rows.append(dict(data.get("dimensions") or {}, _id=data.get("persona_id"), _name=data.get("display_name")))
    n = len(rows)
    L = [f"# Pilot pool audit — {args.pool.name}", "", f"{n} personas. Thin = fewer than {args.min} personas.", ""]

    # 1. page coverage ------------------------------------------------------------------
    L += ["## 1. Page coverage", "",
          "| page | persona filter | eligible | % of pool |", "|---|---|---:|---:|"]
    eligible: dict[str, list[dict]] = {}
    for page, (_url, flt, _kinds) in PAGES.items():
        eligible[page] = [r for r in rows if all(r.get(k) == v for k, v in flt.items())]
        ftxt = ", ".join(f"`{k}` = {v}" for k, v in flt.items()) or "none (everyone)"
        L.append(f"| {page} | {ftxt} | {len(eligible[page])} | {100 * len(eligible[page]) / max(n, 1):.0f} |")
    L.append("")
    thin = []
    for page, (url, _flt, kinds) in PAGES.items():
        sub = eligible[page]
        L += [f"### {page}", "", f"{url} · {len(sub)} eligible personas", "",
              "| visitor kind in the brief | job roles that stand for it | n | |", "|---|---|---:|---|"]
        for kind, roles in kinds.items():
            k = sum(1 for r in sub if r.get("job_role") in roles)
            flag = "thin" if k < args.min else ""
            if flag:
                thin.append(f"{page} · {kind} ({k})")
            L.append(f"| {kind} | {', '.join(roles)} | {k} | {flag} |")
        L += ["", "By company type: " + ", ".join(f"{t} {c}" for t, c in Counter(r.get('tier') for r in sub).most_common()), ""]
    L += ["**Thin cells:** " + ("; ".join(thin) if thin else "none"), ""]

    # 2. coherence ----------------------------------------------------------------------
    def count(pred) -> int:
        return sum(1 for r in rows if pred(r))

    checks = [
        ("Swedish language and culture are Native", count(lambda r: r.get("lang_swedish") != "Native" or r.get("cult_sweden") != "Native")),
        ("Work country is Sweden", count(lambda r: r.get("work_country") != "Sweden")),
        ("Has a job role, a Swedish title and a company type", count(lambda r: not (r.get("job_role") and r.get("job_title_sv") and r.get("tier")))),
        ("Staff role but manager-level seniority", count(lambda r: r.get("job_role") in STAFF_ROLES and r.get("seniority") in MANAGER_SENIORITY)),
        ("Manager role but staff-level seniority", count(lambda r: r.get("job_role") not in STAFF_ROLES and r.get("seniority") not in MANAGER_SENIORITY)),
        # payroll often sits under HR, so HR is accepted for staff
        ("Finance role without a Finance (or, for staff, HR) job function", count(
            lambda r: r.get("job_role") in FINANCE_ROLES and r.get("role_function") != "Finance"
            and not (r.get("job_role") == "Finance or payroll staff" and r.get("role_function") == "HR"))),
        ("Executive or owner without the Executive job function", count(lambda r: r.get("job_role") == "Executive or owner" and r.get("role_function") != "Executive")),
        ("Trades or engineering background in a finance role", count(lambda r: r.get("job_role") in FINANCE_ROLES and r.get("domain") in {"Skilled Trades", "Engineering"})),
        ("Generation does not fit the age bracket", count(lambda r: r.get("demo_generation") not in GENERATION.get(r.get("age_bracket"), set()))),
        ("Swedish native marked as visa holder or undocumented", count(lambda r: r.get("demo_citizenship_status") in {"Visa holder", "Undocumented"})),
        ("Rental-business fields on a non-rental company", count(lambda r: r.get("tier") != "Rental" and any(f in r for f in RENTAL_FIELDS))),
        ("Rental company missing a rental-business field", count(lambda r: r.get("tier") == "Rental" and not all(f in r for f in RENTAL_FIELDS))),
        ("Rental-process audience outside a rental company", count(lambda r: r.get("works_in_rental_process") == YES and r.get("tier") != "Rental")),
        ("Driver who does not drive daily", count(lambda r: r.get("job_role") == "Driver or field worker" and r.get("demo_driver_status") != "Daily driver")),
        ("Device is something other than desktop or mobile", count(lambda r: r.get("device_context") not in {"Desktop, focused", "Mobile, on-the-go"})),
        ("Under 25 with 6 or more years of experience", count(lambda r: r.get("age_bracket") == "18-24" and r.get("years_experience") in {"6-10", "11-20", "20+"})),
        ("Works outside a company (academia, NGO, public sector)", count(lambda r: r.get("company_size") in {"Academia", "NGO", "Public sector"})),
        ("Build-time helper field leaked into a persona", count(lambda r: any(k.startswith("_") and k not in {"_id", "_name"} for k in r))),
        ("Duplicate display names", n - len({r["_name"] for r in rows})),
    ]
    L += ["## 2. Coherence (every row should be 0)", "", "| check | personas failing |", "|---|---:|"]
    L += [f"| {name} | {bad} |" for name, bad in checks]
    L.append("")

    # age requirement -----------------------------------------------------------------
    staff = [r for r in rows if r.get("seniority") not in MANAGER_SENIORITY]
    managers = [r for r in rows if r.get("seniority") in MANAGER_SENIORITY]
    L += ["## Age requirement", "",
          "Required by the study brief. Checked for the whole pool and for managers and staff separately,",
          "so the pool still matches if a task samples only one of them.", "",
          "| age | required % | whole pool % | managers % | staff % | whole pool n |", "|---|---:|---:|---:|---:|---:|"]
    worst = 0.0
    for age, req in AGE_REQUIRED.items():
        def pct(sub: list[dict]) -> float:
            return 100 * sum(1 for r in sub if r.get("age_bracket") == age) / max(len(sub), 1)
        worst = max(worst, abs(pct(rows) - req))
        L.append(f"| {age} | {req} | {pct(rows):.1f} | {pct(managers):.1f} | {pct(staff):.1f} | {sum(1 for r in rows if r.get('age_bracket') == age)} |")
    outside = sum(1 for r in rows if r.get("age_bracket") not in AGE_REQUIRED)
    L += ["", f"Largest gap to the requirement: {worst:.1f} percentage points · personas outside the five brackets: {outside}", ""]

    # 3. shape --------------------------------------------------------------------------
    L += ["## 3. Who is in the pool", ""]
    for title, key in [("Company type (`tier`)", "tier"), ("Kind of visitor (`audience_group`)", "audience_group"),
                       ("Job role (`job_role`)", "job_role"), ("Seniority", "seniority"), ("Age", "age_bracket"),
                       ("Gender", "gender_identity"), ("Company size", "company_size"), ("Device", "device_context"),
                       ("Reason for the visit (`visit_intent`)", "visit_intent"),
                       ("Knowledge of Infobric (`infobric_familiarity`)", "infobric_familiarity"),
                       ("Region in Sweden", "sweden_region")]:
        L += table(title, rows, key)
    L += ["**Company type × kind of visitor**", "",
          "| company type | " + " | ".join(sorted({r.get('audience_group', '—') for r in rows})) + " |"]
    groups = sorted({r.get("audience_group", "—") for r in rows})
    L.append("|---|" + "---:|" * len(groups))
    for tier in sorted({r.get("tier", "—") for r in rows}):
        sub = [r for r in rows if r.get("tier") == tier]
        L.append(f"| {tier} | " + " | ".join(str(sum(1 for r in sub if r.get("audience_group") == g)) for g in groups) + " |")
    L += ["", "**Women by job role** — " + ", ".join(
        f"{role} {100 * sum(1 for r in rows if r.get('job_role') == role and r.get('gender_identity') == 'Woman') / c:.0f}%"
        for role, c in Counter(r.get("job_role") for r in rows).most_common()), ""]

    text = "\n".join(L) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"[done] wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
