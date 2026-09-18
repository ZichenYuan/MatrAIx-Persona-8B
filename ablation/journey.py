#!/usr/bin/env python3
"""Objective journeys for free-visit jobs, and how well the persona self-reported them.

For every trial in one or more harbor job directories this reads:

- the **objective** page sequence browser-use recorded in
  `agent/trajectory.json` (`extra.browser_use.urls`), which exists even when the
  agent failed to write its questionnaire;
- the **self-reported** sequence in the `free_visit.json` artifact, when present;
- the persona's tier, from the persona YAML named in `persona_meta.json`.

It prints one row per trial and a summary (artifact rate, self-report accuracy,
reached-pricing / reached-contact rates, exit sections, pages per visit, by tier),
and can write the rows as JSON for other tooling.

    python ablation/journey.py jobs/fv-probe4 [jobs/other ...] [--json out.json]

Only the standard library is used. Path normalisation mirrors the task verifier
(`application/tasks/web_infobric-free-visit/tests/test_state.py`).
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import pathlib
import re
import statistics
import sys

START_PATH = "/se"
PRICING_FRAGMENTS = ("/pris", "price")
CONTACT_FRAGMENTS = ("/kontakt", "demo", "/prova", "/testa", "trial", "contact", "boka")


def _path(url: str) -> str:
    u = re.sub(r"^https?://[^/]+", "", str(url or "").strip())
    u = u.split("#", 1)[0].split("?", 1)[0].rstrip("/.")
    return u or "/"


def _section(path: str) -> str:
    rest = path[len(START_PATH):].strip("/") if path.startswith(START_PATH) else path.strip("/")
    return rest.split("/", 1)[0] if rest else "home"


def _collapse(urls) -> list[str]:
    out: list[str] = []
    for u in urls:
        if not u or str(u).startswith("about:"):
            continue
        p = _path(u)
        if p == "/":
            continue
        if not out or out[-1] != p:
            out.append(p)
    return out


def _load_json(path: str):
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for kwargs in ({}, {"strict": False}):
        try:
            return json.loads(text, **kwargs)
        except Exception:
            continue
    return None


def _tier(persona_meta: str) -> tuple[str, str]:
    meta = _load_json(persona_meta) or {}
    pid = str(meta.get("persona_id") or "?")
    pp = meta.get("persona_path") or ""
    if pp and os.path.exists(pp):
        m = re.search(r"^\s*tier:\s*(.+?)\s*$", pathlib.Path(pp).read_text(encoding="utf-8"), re.M)
        if m:
            return pid, m.group(1).strip().strip("'\"")
    return pid, "?"


def trial_row(trial_dir: str) -> dict:
    name = os.path.basename(trial_dir.rstrip("/"))
    pid, tier = _tier(os.path.join(trial_dir, "persona_meta.json"))

    traj = _load_json(os.path.join(trial_dir, "agent", "trajectory.json")) or {}
    raw_urls = ((traj.get("extra") or {}).get("browser_use") or {}).get("urls") or []
    objective = _collapse(raw_urls)
    raw_lower = [str(u).lower() for u in raw_urls if u]

    log = os.path.join(trial_dir, "agent", "browser_use.txt")
    steps = 0
    if os.path.exists(log):
        steps = pathlib.Path(log).read_text(encoding="utf-8", errors="replace").count("📍 Step")

    artifacts = glob.glob(os.path.join(trial_dir, "**", "free_visit.json"), recursive=True)
    report = _load_json(artifacts[0]) if artifacts else None
    self_reported = _collapse(report.get("pages_visited") or []) if isinstance(report, dict) else None

    if self_reported is None:
        match = "no_self_report"
    elif self_reported == objective:
        match = "exact"
    elif set(self_reported) <= set(objective):
        match = "subset"
    else:
        match = "differs"

    reward_path = os.path.join(trial_dir, "verifier", "reward.txt")
    reward = pathlib.Path(reward_path).read_text().strip() if os.path.exists(reward_path) else None

    return {
        "trial": name,
        "persona_id": pid,
        "tier": tier,
        "steps": steps,
        "reward": reward,
        "artifact": bool(artifacts),
        "objective_pages": objective,
        "self_reported_pages": self_reported,
        "self_report_match": match,
        "pages_opened": len(objective),
        "distinct_pages": len(set(objective)),
        "exit_page": objective[-1] if objective else None,
        "exit_section": _section(objective[-1]) if objective else None,
        "reached_pricing": any(any(f in u for f in PRICING_FRAGMENTS) for u in raw_lower),
        "reached_contact": any(any(f in u for f in CONTACT_FRAGMENTS) for u in raw_lower),
        "next_step": (report or {}).get("next_step") if isinstance(report, dict) else None,
        "stopped_because": (report or {}).get("stopped_because") if isinstance(report, dict) else None,
    }


def summarise(rows: list[dict]) -> str:
    n = len(rows)
    if not n:
        return "  (no trials)"
    with_art = [r for r in rows if r["artifact"]]
    lines = [
        f"  trials={n}  artifacts={len(with_art)} ({len(with_art)/n:.0%})",
        f"  self-report vs objective (n={len(with_art)}): "
        + ", ".join(f"{k}={v}" for k, v in collections.Counter(r["self_report_match"] for r in with_art).items()),
        f"  reached pricing={sum(r['reached_pricing'] for r in rows)}/{n}  "
        f"reached contact={sum(r['reached_contact'] for r in rows)}/{n}",
        f"  pages opened: mean={statistics.mean(r['pages_opened'] for r in rows):.1f}  "
        f"steps: mean={statistics.mean(r['steps'] for r in rows):.1f}",
        "  exit sections: " + ", ".join(f"{k}={v}" for k, v in collections.Counter(r["exit_section"] for r in rows).most_common()),
    ]
    by_tier = collections.defaultdict(list)
    for r in rows:
        by_tier[r["tier"]].append(r)
    lines.append("  by tier:")
    for tier, rs in sorted(by_tier.items()):
        lines.append(
            f"    {tier:<16} n={len(rs)} artifacts={sum(r['artifact'] for r in rs)} "
            f"pages={statistics.mean(r['pages_opened'] for r in rs):.1f} "
            f"pricing={sum(r['reached_pricing'] for r in rs)} contact={sum(r['reached_contact'] for r in rs)} "
            f"exits={dict(collections.Counter(r['exit_section'] for r in rs))}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("jobs", nargs="+", help="harbor job directories")
    ap.add_argument("--json", help="write rows to this file")
    args = ap.parse_args(argv)

    all_rows: list[dict] = []
    for job in args.jobs:
        trials = sorted(d for d in glob.glob(os.path.join(job, "*__*")) if os.path.isdir(d))
        rows = [trial_row(t) for t in trials]
        print(f"== {job}  ({len(rows)} trials)")
        for r in rows:
            obj = " -> ".join(r["objective_pages"]) or "(none)"
            print(f"  {r['tier']:<16} art={'y' if r['artifact'] else 'N'} steps={r['steps']:>2} "
                  f"match={r['self_report_match']:<14} exit={r['exit_section']:<22} {obj}")
        print(summarise(rows))
        for r in rows:
            r["job"] = job
        all_rows.extend(rows)

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(all_rows, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {len(all_rows)} rows to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
