#!/usr/bin/env python3
"""Audit a persona pool against the Infobric brief and print a Markdown table.

    uv run python persona/scripts/audit_cohort.py persona/datasets/generated-persona-dev-infobric-managers-1000
    uv run python persona/scripts/audit_cohort.py <pool> --out <pool>/audit.md

Rows 1-9 are the same for every set so sets can be compared. The second table covers the
explicit v2 fields (construction role, responsibilities); pools without them show "n/a".
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

KNOWN = {"Aware", "Familiar", "Proficient", "Expert"}
ACTIVE_TOOL = {"Occasional", "Regular", "Power user"}
COMPANY = {"Solo / freelance", "Startup (<50)", "SMB (50-500)", "Mid (500-5k)", "Enterprise (5k+)"}


def project(d: dict) -> bool:
    return d.get("fam_project_management") in KNOWN or d.get("skill_project_management") not in {None, "None"}


def quality(d: dict) -> bool:
    return d.get("fam_quality_assurance") in KNOWN


def depot(d: dict) -> bool:
    return any(d.get(k) in KNOWN for k in ("fam_operations_management", "fam_logistics", "fam_supply_chain"))


def site(d: dict) -> bool:
    return any(d.get(k) in KNOWN for k in ("fam_civil_engineering", "fam_structural_engineering")) or any(
        d.get(k) in ACTIVE_TOOL for k in ("tool_autocad", "tool_revit")
    )


PM = ["fam_project_management", "skill_project_management"]
QA = ["fam_quality_assurance"]
DEPOT = ["fam_operations_management", "fam_logistics", "fam_supply_chain"]
SITE = ["fam_civil_engineering", "fam_structural_engineering", "tool_autocad", "tool_revit"]

# (label, fields the check reads, predicate). A row prints n/a when no persona has any field.
CORE = [
    ("Construction experience", ["ind_construction"], lambda d: d.get("ind_construction") in {"Experienced", "Veteran"}),
    ("Swedish language and culture", ["lang_swedish", "cult_sweden"], lambda d: d.get("lang_swedish") == "Native" and d.get("cult_sweden") == "Native"),
    ("Manager, Director, C-suite, or Founder", ["seniority"], lambda d: d.get("seniority") in {"Manager", "Director", "C-suite", "Founder"}),
    ("Full-time or self-employed", ["demo_employment_status"], lambda d: d.get("demo_employment_status") in {"Full-time", "Self-employed"}),
    ("Project-management knowledge or skill", PM, project),
    ("Quality assurance, used as an HQSE proxy", QA, quality),
    ("Operations, logistics, or supply-chain knowledge", DEPOT, depot),
    ("Civil, structural, AutoCAD, or Revit signal", SITE, site),
    ("All four available interest signals", PM + QA + DEPOT + SITE, lambda d: project(d) and quality(d) and depot(d) and site(d)),
    ("Works at a company (not academia, NGO, public sector)", ["company_size"], lambda d: d.get("company_size") in COMPANY),
    ("Engineering, Operations, or Executive job function", ["role_function"], lambda d: d.get("role_function") in {"Engineering", "Operations", "Executive"}),
    ("Some English", ["english_proficiency"], lambda d: d.get("english_proficiency") not in {None, "None"}),
]

RESP = ["resp_project_delivery", "resp_safety_hseq", "resp_heavy_equipment", "resp_rental_operations", "resp_tools_assets"]

EXPLICIT = [
    ("Work country = Sweden", ["work_country"], lambda d: d.get("work_country") == "Sweden"),
    ("Explicit construction role", ["construction_role"], lambda d: bool(d.get("construction_role"))),
    ("Swedish job title", ["job_title_sv"], lambda d: bool(d.get("job_title_sv"))),
    ("Owns project delivery", RESP[:1], lambda d: d.get("resp_project_delivery") == "Owns"),
    ("Owns or shares safety / HSEQ", RESP[1:2], lambda d: d.get("resp_safety_hseq") in {"Owns", "Shares"}),
    ("Owns or shares heavy machines on site", RESP[2:3], lambda d: d.get("resp_heavy_equipment") in {"Owns", "Shares"}),
    ("Owns or shares rental management", RESP[3:4], lambda d: d.get("resp_rental_operations") in {"Owns", "Shares"}),
    ("Owns or shares tools and assets", RESP[4:], lambda d: d.get("resp_tools_assets") in {"Owns", "Shares"}),
    ("Owns at least one of the five responsibilities", RESP, lambda d: any(d.get(k) == "Owns" for k in RESP)),
    ("Involved in all five responsibilities", RESP, lambda d: all(d.get(k) in {"Owns", "Shares"} for k in RESP)),
]


def load(pool: Path) -> list[dict]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(pool.glob("persona_*.yaml"))]


def table(rows: list[dict], checks, n: int) -> list[str]:
    out = ["| Criterion | Result |", "|---|---|"]
    for label, fields, fn in checks:
        if not any(f in d for d in rows for f in fields):
            out.append(f"| {label} | n/a (fields absent) |")
            continue
        out.append(f"| {label} | {sum(1 for d in rows if fn(d)):,} / {n:,} |")
    return out


def dist(rows: list[dict], key: str) -> str:
    c = Counter(d.get(key, "—") for d in rows)
    return ", ".join(f"{k} {v}" for k, v in c.most_common())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pool", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="write Markdown here instead of stdout")
    args = ap.parse_args()

    personas = load(args.pool)
    rows = [p.get("dimensions", {}) for p in personas]
    n = len(rows)
    dims_per_persona = sorted(len(d) for d in rows)
    L = [f"# Audit — `{args.pool.name}`", "",
         f"{n:,} personas · {dims_per_persona[0]}–{dims_per_persona[-1]} dimensions each", "",
         "## Brief criteria", ""]
    L += table(rows, CORE, n)
    L += ["", "## Explicit construction fields (v2 overlays)", ""]
    L += table(rows, EXPLICIT, n)
    L += ["", "## Key distributions", ""]
    for key in ("tier", "construction_role", "seniority", "company_size", "role_function", "gender_identity",
                "age_bracket", "sweden_region", "work_setting", "purchasing_authority", "digital_site_tools_today"):
        if any(key in d for d in rows):
            L.append(f"- `{key}`: {dist(rows, key)}")
    text = "\n".join(L) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
