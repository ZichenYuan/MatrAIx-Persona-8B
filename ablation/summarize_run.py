#!/usr/bin/env python3
"""One-command summary of a page-audit v2 job: what the partner asked for, and the
quality gates the case study needs, read straight from each trial's quality.json.

    python ablation/summarize_run.py jobs/<job-dir> [--out report.md] [--json numbers.json]

Coverage and failures come from each trial's result.json; everything else from
verifier/quality.json (written by tests/test_state.py). The exit rate is set next to
the partner's Clarity "Quick Backs" for the same page (ablation/ground_truth/analytics_90d.json).
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYTICS = HERE / "ground_truth" / "analytics_90d.json"
DIMS = ["understanding", "language_relevance", "practical_value", "trust", "next_step_confidence", "next_step_ease"]
EXTRA_SCORES = ["cta_match", "contact_likelihood"]
PERSONA_DIMS = ["traffic_segment", "audience_group", "tier", "visit_intent", "infobric_familiarity"]
TRUST_LADDER = ["trust_email_guide", "trust_callback", "trust_demo_week", "trust_pilot_data"]
TRUST_ACTS = TRUST_LADDER + ["trust_claim_unchecked"]
TRUST_TITLES = {"trust_email_guide": "Would give a work email for a guide", "trust_callback": "Would ask for a call-back",
                "trust_demo_week": "Would book a demo this week", "trust_pilot_data": "Would run a pilot on own data this month",
                "trust_claim_unchecked": "Would accept the proof claim unchecked"}
COLLAPSED_SD = 0.3  # a 1-5 scale whose sd falls below this is not separating anyone


def load_trials(job: Path) -> list[dict]:
    rows = []
    for res in sorted(job.glob("*/result.json")):
        try:
            r = json.loads(res.read_text())
        except json.JSONDecodeError:
            continue
        row = {"trial": res.parent.name, "finished": bool(r.get("finished_at"))}
        exc = r.get("exception_info")
        row["exception"] = exc.get("exception_type") if isinstance(exc, dict) and exc else None
        row["reward"] = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        q = res.parent / "verifier" / "quality.json"
        row["quality"] = json.loads(q.read_text()) if q.is_file() else None
        rows.append(row)
    return rows


def mean_sd(values: list[float]) -> tuple[float | None, float | None]:
    vals = [float(v) for v in values if isinstance(v, (int, float))]
    if not vals:
        return None, None
    return statistics.mean(vals), (statistics.pstdev(vals) if len(vals) > 1 else 0.0)


def eta_squared(values: list, groups: list) -> float | None:
    """Share of variance in `values` explained by `groups` (one-way ANOVA η²)."""
    pairs = [(float(v), str(g)) for v, g in zip(values, groups) if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(pairs) < 3:
        return None
    grand = statistics.mean(v for v, _ in pairs)
    by: dict[str, list[float]] = collections.defaultdict(list)
    for v, g in pairs:
        by[g].append(v)
    ss_between = sum(len(vs) * (statistics.mean(vs) - grand) ** 2 for vs in by.values())
    ss_total = sum((v - grand) ** 2 for v, _ in pairs)
    return ss_between / ss_total if ss_total else 0.0


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "n/a"


def fmt(x: float | None, nd: int = 2) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def share_table(rows: list[dict], key: str, group: str = "audience_group") -> tuple[collections.Counter, dict]:
    overall = collections.Counter(str(r[key]) for r in rows if r.get(key) is not None)
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        if r.get(key) is not None:
            by[r.get(group) or "unknown"][str(r[key])] += 1
    return overall, by


def flatten(q: dict) -> dict:
    """quality.json -> one flat row per trial."""
    p, e, f, g, c, s, d = (q.get(k) or {} for k in ("persona", "exit", "fidelity", "grounding", "cta", "scores_in_browse", "decision"))
    row = {k: p.get(k) for k in PERSONA_DIMS}
    row.update({
        "json_health": q.get("json_health"), "instrument_version": q.get("instrument_version"), "variant": q.get("variant"),
        "device": q.get("device_reviewed"), "unmapped": len(q.get("unmapped_values") or []),
        "left_early": bool(e.get("left_early")), "would_continue": e.get("would_continue"),
        "fidelity_ok": f.get("arrived_with_matches_persona"),
        "claims_grounded_share": g.get("claims_grounded_share"), "phrases_grounded_share": g.get("phrases_grounded_share"),
        "ungrounded": len(g.get("ungrounded_quotes") or []),
        "cta_inspected": c.get("cta_inspected"), "cta_url_ok": c.get("cta_url_ok"), "cta_label_grounded": c.get("cta_label_grounded"),
        "next_step": d.get("next_step"), "converted": d.get("converted"), "basis_primary": d.get("basis_primary"), "trust_action": d.get("trust_action"),
        "missing_info": q.get("missing_info") or [], "weakest": (q.get("positions") or {}).get("weakest"), "strongest": (q.get("positions") or {}).get("strongest"),
    })
    for k in DIMS + EXTRA_SCORES:
        row[k] = s.get(k)
    row["post_hoc"] = q.get("scores_post_hoc") or None
    row["trust_ladder"] = s.get("trust_ladder")
    row["trust_ladder_consistent"] = s.get("trust_ladder_consistent")
    row["trust_acts_answers"] = {k: s.get(k) for k in TRUST_ACTS}
    return row


def build(job: Path) -> tuple[str, dict]:
    trials = load_trials(job)
    cfg = json.loads((job / "config.json").read_text()) if (job / "config.json").is_file() else {}
    launched = len(cfg.get("agents") or []) or len(trials)
    finished = [t for t in trials if t["finished"]]
    passed = [t for t in finished if t["reward"] == 1.0]
    failed = [t for t in finished if t["reward"] != 1.0]
    exc_mix = collections.Counter(t["exception"] or "verifier scored 0 (no exception)" for t in failed)
    rows = [flatten(t["quality"]) for t in finished if t["quality"]]
    page = (finished[0]["quality"].get("page_id") if finished and finished[0]["quality"] else None) or "homepage"
    numbers: dict = {"job": job.name, "page": page, "launched": launched, "finished": len(finished), "passed": len(passed), "failed": len(failed)}
    out: list[str] = []
    w = out.append

    w(f"# {page}: {len(finished)} of {launched} trials finished — {job.name}\n")
    w("## 1. Coverage (pipeline health — gate, not a result)\n")
    w(f"- Launched {launched}, finished {len(finished)}, passed verifier {len(passed)} ({pct(len(passed), len(finished))}), failed {len(failed)}")
    for k, n in exc_mix.most_common():
        w(f"  - {n} × {k}")
    health = collections.Counter(r["json_health"] for r in rows)
    w(f"- Artifact parse: " + ", ".join(f"{k} {n}" for k, n in health.most_common()) + f" (clean rate {pct(health.get('clean', 0), len(rows))})")
    w(f"- Instrument {sorted({r['instrument_version'] for r in rows})}, variant {sorted({str(r['variant']) for r in rows})}, device {dict(collections.Counter(r['device'] for r in rows))}")
    w(f"- Values the verifier could not map onto the answer set: {sum(r['unmapped'] for r in rows)} across {sum(1 for r in rows if r['unmapped'])} trials\n")
    numbers["json_health"] = dict(health)

    w("## 2. Who was simulated (finished trials)\n")
    for dim in PERSONA_DIMS:
        cnt = collections.Counter(str(r[dim]) for r in rows)
        w(f"- **{dim}**: " + "; ".join(f"{k} {n} ({pct(n, len(rows))})" for k, n in cnt.most_common()))
    w("")

    w("## 3. Did they stay? Exit after the first screen vs the partner's analytics\n")
    exits = sum(1 for r in rows if r["left_early"])
    cont = collections.Counter(str(r["would_continue"]) for r in rows)
    w(f"- Left after the first screen (`left_early`): {exits} of {len(rows)} = **{pct(exits, len(rows))}**")
    w(f"- Would keep reading (`would_continue`): " + ", ".join(f"{k} {n}" for k, n in cont.most_common()))
    numbers["exit_rate"] = exits / len(rows) if rows else None
    gt = json.loads(ANALYTICS.read_text()).get("pages", {}).get(page, {}) if ANALYTICS.is_file() else {}
    cl, ga = gt.get("clarity") or {}, gt.get("ga4") or {}
    if cl or ga:
        w(f"- Partner ground truth for this page (90 days): Clarity Quick Backs **{fmt(cl.get('quick_backs'), 3)}** "
          f"({cl.get('quick_backs_sessions')} sessions), GA4 engaged share {fmt(ga.get('engaged_share'), 3)}, "
          f"avg engagement {ga.get('avg_engagement_sec')} s, scroll depth {fmt(cl.get('scroll_depth'), 3)}")
        w("- Read with care: a Quick Back is a real session that left within seconds (bots excluded, wrong-clicks included); "
          "`left_early` is a persona that read the first screen and chose not to continue. Same direction, not the same event.")
        numbers["ground_truth"] = {"quick_backs": cl.get("quick_backs"), "engaged_share": ga.get("engaged_share")}
    _, by = share_table(rows, "left_early")
    w("\n| Visitor kind | n | left early | would continue = yes |")
    w("|---|---:|---:|---:|")
    for grp, cnt in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(cnt.values()); yes = sum(1 for r in rows if (r["audience_group"] or "unknown") == grp and str(r["would_continue"]).lower() == "yes")
        w(f"| {grp} | {n} | {pct(cnt.get('True', 0), n)} | {pct(yes, n)} |")
    w("")

    if any(r.get("traffic_segment") for r in rows):
        w("| Traffic segment | n | left early | would continue = yes | next step: leave | go to login |")
        w("|---|---:|---:|---:|---:|---:|")
        for seg, cnt in sorted(collections.Counter(r["traffic_segment"] or "unknown" for r in rows).items(), key=lambda kv: -kv[1]):
            sub = [r for r in rows if (r["traffic_segment"] or "unknown") == seg]
            w(f"| {seg} | {cnt} | {pct(sum(1 for r in sub if r['left_early']), cnt)} | "
              f"{pct(sum(1 for r in sub if str(r['would_continue']).lower() == 'yes'), cnt)} | "
              f"{pct(sum(1 for r in sub if r['next_step'] == 'leave'), cnt)} | {pct(sum(1 for r in sub if r['next_step'] == 'go_to_login'), cnt)} |")
        w("")
        numbers["exit_by_segment"] = {seg: sum(1 for r in rows if (r["traffic_segment"] or "unknown") == seg and r["left_early"]) for seg in {r["traffic_segment"] or "unknown" for r in rows}}

    acts_present = [r for r in rows if any((r.get("trust_acts_answers") or {}).get(k) in ("yes", "no") for k in TRUST_ACTS)]
    if acts_present:
        w("## 3b. Trust as a ladder of commitments (yes/no, rising cost) plus one belief item\n")
        n_a = len(acts_present)
        for k in TRUST_ACTS:
            yes = sum(1 for r in acts_present if r["trust_acts_answers"].get(k) == "yes")
            unk = sum(1 for r in acts_present if r["trust_acts_answers"].get(k) not in ("yes", "no"))
            w(f"- **{TRUST_TITLES[k]}**: yes {pct(yes, n_a)} of {n_a}" + (f" ({unk} unanswered)" if unk else ""))
        laddered = [r for r in acts_present if isinstance(r.get("trust_ladder"), (int, float))]
        counts = [r["trust_ladder"] for r in laddered]
        if counts:
            m, sd = mean_sd(counts)
            inconsistent = sum(1 for r in laddered if r.get("trust_ladder_consistent") == "no")
            w(f"- **Rungs accepted (0-4)**: mean {fmt(m)}, sd {fmt(sd)}, distribution " + ", ".join(f"{i}: {sum(1 for c in counts if int(c) == i)}" for i in range(5))
              + f"; inconsistent ladders (a yes above a no) {inconsistent} of {len(counts)}")
            numbers["trust_ladder"] = {"n": len(counts), "mean": m, "sd": sd,
                                       "eta2_audience": eta_squared(counts, [r["audience_group"] for r in laddered]),
                                       "eta2_segment": eta_squared(counts, [r.get("traffic_segment") for r in laddered]),
                                       "eta2_intent": eta_squared(counts, [r.get("visit_intent") for r in laddered])}
            w(f"- η² by visitor kind {fmt(numbers['trust_ladder']['eta2_audience'])} · by traffic segment {fmt(numbers['trust_ladder']['eta2_segment'])} · by visit intent {fmt(numbers['trust_ladder']['eta2_intent'])}")
            w("\n| Group | n | mean rungs | " + " | ".join(TRUST_TITLES[k].replace("Would ", "") for k in TRUST_ACTS) + " |")
            w("|---|---:|---:|" + "---:|" * len(TRUST_ACTS))
            for dim in ("traffic_segment", "audience_group", "visit_intent"):
                for g, cnt in collections.Counter(r.get(dim) or "unknown" for r in laddered).most_common():
                    sub = [r for r in laddered if (r.get(dim) or "unknown") == g]
                    w(f"| {g} | {cnt} | {fmt(mean_sd([r['trust_ladder'] for r in sub])[0])} | "
                      + " | ".join(pct(sum(1 for r in sub if r['trust_acts_answers'].get(k) == 'yes'), cnt) for k in TRUST_ACTS) + " |")
        w("")

    w("## 4. The six partner dimensions (1-5) and the two follow-ups\n")
    w("| Dimension | n | mean | sd | " + " | ".join(f"{k} (1-5 share)" for k in ["1", "2", "3", "4", "5"]) + " | note |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    numbers["scores"] = {}
    for k in DIMS + EXTRA_SCORES:
        vals = [r[k] for r in rows if isinstance(r[k], (int, float))]
        m, sd = mean_sd(vals)
        dist = collections.Counter(int(v) for v in vals)
        note = "**collapsed** (sd < 0.3)" if sd is not None and sd < COLLAPSED_SD and len(vals) >= 20 else ""
        w(f"| {k} | {len(vals)} | {fmt(m)} | {fmt(sd)} | " + " | ".join(pct(dist.get(i, 0), len(vals)) for i in range(1, 6)) + f" | {note} |")
        numbers["scores"][k] = {"n": len(vals), "mean": m, "sd": sd, "dist": {str(i): dist.get(i, 0) for i in range(1, 6)}}
    w("\n### By visitor kind (mean)\n")
    groups = [g for g, _ in collections.Counter(r["audience_group"] or "unknown" for r in rows).most_common()]
    w("| Visitor kind | n | " + " | ".join(DIMS + EXTRA_SCORES) + " |")
    w("|---|---:|" + "---:|" * (len(DIMS) + len(EXTRA_SCORES)))
    numbers["scores_by_audience"] = {}
    for g in groups:
        sub = [r for r in rows if (r["audience_group"] or "unknown") == g]
        means = {k: mean_sd([r[k] for r in sub])[0] for k in DIMS + EXTRA_SCORES}
        numbers["scores_by_audience"][g] = {"n": len(sub), **means}
        w(f"| {g} | {len(sub)} | " + " | ".join(fmt(means[k]) for k in DIMS + EXTRA_SCORES) + " |")
    w("")

    scored = [r for r in rows if r.get("post_hoc")]
    if scored:
        w("## 4b. In-browse vs scored after the visit (Finding 1 replication)\n")
        w(f"{len(scored)} of {len(rows)} trials re-scored outside the browser by the same model from the persona text plus the persona's own notes "
          "(application/scripts/score_audit.py). η² = share of score variance explained by the persona dimension; 0.01 small, 0.06 medium, 0.14 large.\n")
        w("| Score | mean in-browse | sd | mean scored | sd | η² visitor kind (in / scored) | η² tier (in / scored) | η² visit intent (in / scored) | values used (scored) |")
        w("|---|---:|---:|---:|---:|---:|---:|---:|---|")
        numbers["post_hoc"] = {}
        for k in DIMS + EXTRA_SCORES:
            ib = [r[k] for r in scored]; ph = [r["post_hoc"].get(k) for r in scored]
            mi, si = mean_sd(ib); mp, sp = mean_sd(ph)
            e = {dim: (eta_squared(ib, [r[dim] for r in scored]), eta_squared(ph, [r[dim] for r in scored])) for dim in ("audience_group", "tier", "visit_intent")}
            used = sorted({int(v) for v in ph if isinstance(v, (int, float))})
            w(f"| {k} | {fmt(mi)} | {fmt(si)} | {fmt(mp)} | {fmt(sp)} | " + " | ".join(f"{fmt(a)} / {fmt(b)}" for a, b in e.values()) + f" | {used} |")
            numbers["post_hoc"][k] = {"mean_in_browse": mi, "sd_in_browse": si, "mean_scored": mp, "sd_scored": sp,
                                      "eta2": {dim: {"in_browse": a, "scored": b} for dim, (a, b) in e.items()}}
        w("\n### Scored after the visit, by visitor kind (mean)\n")
        w("| Visitor kind | n | " + " | ".join(DIMS + EXTRA_SCORES) + " |")
        w("|---|---:|" + "---:|" * (len(DIMS) + len(EXTRA_SCORES)))
        for g in groups:
            sub = [r for r in scored if (r["audience_group"] or "unknown") == g]
            if not sub:
                continue
            w(f"| {g} | {len(sub)} | " + " | ".join(fmt(mean_sd([r["post_hoc"].get(k) for r in sub])[0]) for k in DIMS + EXTRA_SCORES) + " |")
        w("")

    w("## 5. What they would do next\n")
    for key, title in (("next_step", "Next step"), ("trust_action", "Needed before going further"), ("basis_primary", "Main basis of the decision")):
        overall, by = share_table(rows, key)
        w(f"- **{title}**: " + "; ".join(f"{k} {n} ({pct(n, len(rows))})" for k, n in overall.most_common()))
        numbers[key] = dict(overall)
    conv = sum(1 for r in rows if r["converted"])
    w(f"- Converted (contact / demo / trial as the next step): {conv} of {len(rows)} = {pct(conv, len(rows))}")
    missing = collections.Counter(m for r in rows for m in r["missing_info"])
    w(f"- Information they missed most: " + "; ".join(f"{k} {n}" for k, n in missing.most_common(8)))
    weak = collections.Counter(str(r["weakest"]) for r in rows); strong = collections.Counter(str(r["strongest"]) for r in rows)
    w(f"- Weakest part of the page: " + ", ".join(f"{k} {n}" for k, n in weak.most_common(4)) + f" · strongest: " + ", ".join(f"{k} {n}" for k, n in strong.most_common(4)))
    w("\n| Visitor kind | " + " | ".join(k for k, _ in share_table(rows, 'next_step')[0].most_common()) + " |")
    _, by = share_table(rows, "next_step"); heads = [k for k, _ in share_table(rows, "next_step")[0].most_common()]
    w("|---|" + "---:|" * len(heads))
    for g in groups:
        cnt = by.get(g, collections.Counter()); n = sum(cnt.values())
        w(f"| {g} | " + " | ".join(pct(cnt.get(h, 0), n) for h in heads) + " |")
    w("")

    w("## 6. Quality gates for the case study\n")
    fid = [r["fidelity_ok"] for r in rows if r["fidelity_ok"] is not None]
    w(f"- Persona fidelity (`arrived_with` matches the persona's own reason for visiting): {pct(sum(1 for v in fid if v), len(fid))} of {len(fid)}")
    cg, _ = mean_sd([r["claims_grounded_share"] for r in rows]); pg, _ = mean_sd([r["phrases_grounded_share"] for r in rows])
    w(f"- Grounding: quoted claims found on the page {fmt(cg, 3)}, quoted phrases found on the page {fmt(pg, 3)}; "
      f"trials with any ungrounded quote {sum(1 for r in rows if r['ungrounded'])} of {len(rows)}")
    ins = sum(1 for r in rows if r["cta_inspected"]); ok = sum(1 for r in rows if r["cta_url_ok"]); lab = sum(1 for r in rows if r["cta_label_grounded"])
    w(f"- Primary button: inspected {pct(ins, len(rows))}, landed on the expected page {pct(ok, len(rows))}, label quoted correctly {pct(lab, len(rows))}")
    numbers["quality"] = {"fidelity_rate": (sum(1 for v in fid if v) / len(fid)) if fid else None, "claims_grounded": cg, "phrases_grounded": pg,
                          "cta_inspected": ins / len(rows) if rows else None, "cta_url_ok": ok / len(rows) if rows else None}
    w("")
    return "\n".join(out), numbers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", type=Path)
    ap.add_argument("--out", type=Path, help="write the markdown report here")
    ap.add_argument("--json", type=Path, help="write the numbers here")
    a = ap.parse_args()
    md, numbers = build(a.job)
    if a.out:
        a.out.write_text(md); print(f"wrote {a.out}", file=sys.stderr)
    else:
        print(md)
    if a.json:
        a.json.write_text(json.dumps(numbers, indent=2, default=str)); print(f"wrote {a.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
