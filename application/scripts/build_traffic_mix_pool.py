#!/usr/bin/env python3
"""Derive a traffic-mix persona pool from the pilot-full pool (ablation arm 1).

Why: the pilot-full pool is 100% prospects, and the homepage's first screen speaks to
every one of them, so nobody leaves (0% vs 44% Quick Backs in the partner's analytics).
Real homepage sessions are mostly not prospects: 51% carry a login event, 43% are
returning users, and Quick Backs also count job seekers, suppliers, students and
mis-clicks. This script keeps every persona's identity and job but assigns each a
*traffic segment* with analytics-like proportions, overriding only the fields that say
why the person is on infobric.com today:

  prospect            40%  unchanged (the baseline condition)
  existing_customer   45%  company already uses an Infobric product; came to log in / support
  job_seeker           5%  looking for the careers page
  supplier_partner     3%  wants to sell something to Infobric
  student_researcher   3%  writing an assignment about the company
  misclick             4%  landed here from a search result or an ad by mistake

Each non-prospect gets `traffic_segment` (grouping key) and `arrival_note` (rendered at the
end of the persona prompt under "Other attributes", after the job fields). The manifest is
rewritten with the two new overlay dimensions so the Playground can stratify on
`traffic_segment` and the report can group by it.

    python application/scripts/build_traffic_mix_pool.py \
        [--source persona/datasets/generated-persona-dev-infobric-pilot-full] \
        [--out persona/datasets/generated-persona-dev-infobric-traffic-mix] [--seed 7]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

MIX = [  # (segment, share) - shares sum to 1.0
    ("prospect", 0.40),
    ("existing_customer", 0.45),
    ("job_seeker", 0.05),
    ("supplier_partner", 0.03),
    ("student_researcher", 0.03),
    ("misclick", 0.04),
]
SEGMENT_LABEL = {
    "prospect": "Prospect (evaluating a supplier)",
    "existing_customer": "Existing customer (login or support)",
    "job_seeker": "Job seeker",
    "supplier_partner": "Supplier or partner (selling to Infobric)",
    "student_researcher": "Student or researcher",
    "misclick": "Mis-click from a search result or an ad",
}
VISIT_INTENT = {
    "existing_customer": "Existing customer: came to log in or reach support, not to evaluate",
    "job_seeker": "Looking for job openings at Infobric",
    "supplier_partner": "Wants to sell services or products to Infobric",
    "student_researcher": "Researching the company for a school or university assignment",
    "misclick": "Landed here by mistake from a search result or an ad",
}
FAMILIARITY = {
    "existing_customer": "Uses Infobric at work today",
    "job_seeker": "Has heard the name but knows nothing more",
    "misclick": "Has never heard of Infobric",
}
OFFERINGS = ["IT consulting", "recruitment services", "electronic components for tracking hardware", "marketing services", "office cleaning"]
MISCLICK_NOTES = [
    "You searched for a free driving-log app for your private car and clicked this result expecting a consumer app.",
    "You clicked an ad while looking for something else entirely and did not mean to come here.",
    "You were looking for the site where you register your attendance at a building site with your ID06 card and thought this was it.",
    "You searched for a used machine to buy and this result looked like a marketplace.",
]


def product_for(dims: dict) -> str:
    part = "Part of my job"
    if dims.get("works_in_rental_process") == part:
        return "Hyrma (rental management)"
    if dims.get("deals_with_vehicles") == part or dims.get("deals_with_driving_logs") == part:
        return "Infobric Fleet (vehicle tracking and driving logs)"
    if dims.get("deals_with_tools_equipment") == part:
        return "Infobric Equipment (tool and machine tracking)"
    return "Infobric Site (site access and attendance)"


def overrides(segment: str, dims: dict, rng: random.Random) -> dict:
    out = {"traffic_segment": SEGMENT_LABEL[segment]}
    if segment == "prospect":
        return out
    out["visit_intent"] = VISIT_INTENT[segment]
    if segment in FAMILIARITY:
        out["infobric_familiarity"] = FAMILIARITY[segment]
    if segment == "existing_customer":
        purpose = "log in to it" if rng.random() < 0.7 else "find the support phone number"
        out["arrival_note"] = (
            f"Your company already uses {product_for(dims)} from Infobric. You opened infobric.com to {purpose}. "
            "You are not shopping for anything today; if the page does not get you there quickly, you go elsewhere "
            "(a bookmark, the app, a phone call)."
        )
    elif segment == "job_seeker":
        out["arrival_note"] = (
            "You are looking for a new job and heard Infobric is hiring in your region. You came to find their careers "
            "page and open positions; the products themselves are not your concern today."
        )
    elif segment == "supplier_partner":
        out["arrival_note"] = (
            f"You work for a company that sells {rng.choice(OFFERINGS)} and want to find the right person at Infobric "
            "to pitch to. You are here for a name, an email address or a partner page, not for their products."
        )
    elif segment == "student_researcher":
        out["arrival_note"] = (
            "You are writing an assignment about digitalisation in the construction industry and want facts about the "
            "company: what it does, how big it is, its history. You will not buy anything."
        )
    elif segment == "misclick":
        out["arrival_note"] = rng.choice(MISCLICK_NOTES)
    return out


def rewrite_yaml(text: str, new_dims: dict) -> str:
    """Set/append keys inside the top-level `dimensions:` block without a YAML round-trip
    (keeps the file byte-identical elsewhere)."""
    lines = text.split("\n")
    # find the dimensions block: from 'dimensions:' to the next top-level key
    start = next(i for i, ln in enumerate(lines) if ln.startswith("dimensions:"))
    end = start + 1
    while end < len(lines) and (lines[end].startswith("  ") or lines[end].strip() == ""):
        end += 1
    block = lines[start + 1:end]
    done = set()
    for i, ln in enumerate(block):
        m = re.match(r"^  ([A-Za-z0-9_]+):", ln)
        if m and m.group(1) in new_dims:
            block[i] = f"  {m.group(1)}: {yaml_scalar(new_dims[m.group(1)])}"
            done.add(m.group(1))
    # drop trailing blank lines inside the block before appending
    while block and block[-1].strip() == "":
        block.pop()
    for key, value in new_dims.items():
        if key not in done:
            block.append(f"  {key}: {yaml_scalar(value)}")
    return "\n".join(lines[:start + 1] + block + lines[end:])


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # a JSON string is a valid YAML double-quoted scalar


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="persona/datasets/generated-persona-dev-infobric-pilot-full")
    ap.add_argument("--out", default="persona/datasets/generated-persona-dev-infobric-traffic-mix")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    src = (REPO / a.source).resolve()
    out = REPO / a.out
    if out.exists():
        if not a.force:
            sys.exit(f"{out} exists; pass --force to rebuild")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    manifest = json.loads((src / "manifest.json").read_text())
    personas = manifest["personas"]
    rng = random.Random(a.seed)
    order = list(range(len(personas)))
    rng.shuffle(order)
    # proportional assignment in shuffled order (largest-remainder on the shares)
    n = len(personas)
    counts = {seg: int(share * n) for seg, share in MIX}
    for seg, _ in sorted(MIX, key=lambda s: -(s[1] * n - int(s[1] * n))):
        if sum(counts.values()) >= n:
            break
        counts[seg] += 1
    assignment: dict[int, str] = {}
    pos = 0
    for seg, _ in MIX:
        for idx in order[pos:pos + counts[seg]]:
            assignment[idx] = seg
        pos += counts[seg]

    seg_counter: dict[str, int] = {}
    for idx, entry in enumerate(personas):
        seg = assignment.get(idx, "prospect")
        seg_counter[seg] = seg_counter.get(seg, 0) + 1
        src_yaml = (REPO / entry["path"]).resolve() if not Path(entry["path"]).is_absolute() else Path(entry["path"])
        if not src_yaml.is_file():
            src_yaml = src / Path(entry["path"]).name
        new_dims = overrides(seg, entry.get("dimensions") or {}, rng)
        text = src_yaml.read_text(encoding="utf-8")
        (out / src_yaml.name).write_text(rewrite_yaml(text, new_dims), encoding="utf-8")
        entry["path"] = f"{a.out}/{src_yaml.name}"
        entry.setdefault("dimensions", {}).update(new_dims)
        entry["traffic_segment"] = seg

    manifest["kind"] = "infobric-traffic-mix"
    manifest["name"] = "Infobric pilot — traffic mix"
    manifest["description"] = (
        "The pilot-full personas with an analytics-like traffic mix: 40% prospects (unchanged), 45% existing customers "
        "coming to log in or reach support, 15% wrong-fit visitors (job seekers, suppliers, students, mis-clicks). "
        f"Derived from {a.source} with seed {a.seed} by application/scripts/build_traffic_mix_pool.py."
    )
    manifest["derived_from"] = a.source
    manifest["traffic_mix"] = {seg: {"share": share, "count": seg_counter.get(seg, 0)} for seg, share in MIX}
    manifest["created_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    manifest["overlay_dimensions"] = list(manifest.get("overlay_dimensions") or []) + [
        {"id": "traffic_segment", "label": "Why you are on infobric.com today", "values": [SEGMENT_LABEL[s] for s, _ in MIX]},
        {"id": "arrival_note", "label": "How you got here today", "values": []},
    ]
    for key in ("overlay_ids", "dimension_ids"):
        manifest[key] = list(manifest.get(key) or []) + ["traffic_segment", "arrival_note"]
    manifest["dimension_count"] = len(manifest["dimension_ids"])
    # extend the existing overlay value lists so stratification UIs know the new values
    for row in manifest["overlay_dimensions"]:
        if row["id"] == "visit_intent":
            row["values"] = sorted(set(row["values"]) | set(VISIT_INTENT.values()))
        if row["id"] == "infobric_familiarity":
            row["values"] = sorted(set(row["values"]) | set(FAMILIARITY.values()))
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    for extra in ("README.md",):
        if (src / extra).is_file():
            shutil.copyfile(src / extra, out / extra)
    print(f"wrote {n} personas to {out}\nsegments: " + ", ".join(f"{s} {seg_counter.get(s, 0)}" for s, _ in MIX), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
