#!/usr/bin/env python3
"""Build a synthetic persona cohort from a YAML config: pin early DAG nodes, draw,
filter late nodes, enforce coherence rules, fill per-cell quotas (drawing more for weak
cells up to `max_draws_per_cell`), stamp overlays (constant / balanced / `shares_by` a
parent field), apply overrides, and write a Playground-visible pool (one YAML per persona
+ manifest.json) plus a validation.md report.

    uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_managers.yaml
    uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_managers_v2.yaml

Why not `generate_dev_personas.py --filter …`? Pinning a node only conditions the
nodes sampled AFTER it. Pinning late nodes (seniority, years_experience) leaves age
drawn from the general prior — toddler CEOs. This script pins early nodes (as
cells with shares, so quotas are exact) and rejection-filters late ones, which
keeps the joint coherent. See PLAN.md §4.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (REPO_ROOT, REPO_ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from matraix.persona_display_name import assign_cohort_display_names  # noqa: E402
from matraix.persona_generator import (  # noqa: E402
    DEFAULT_PERSONA_VERSION,
    _dag_sampler,
    _persona_entry,
    write_persona_dataset,
)

POOL_PREFIX = "generated-persona-dev"


# --- helpers -----------------------------------------------------------------
def largest_remainder(shares: dict, total: int) -> dict:
    """Integer quotas that sum exactly to `total`, proportional to `shares`."""
    s = float(sum(shares.values()))
    raw = {k: total * float(v) / s for k, v in shares.items()}
    quotas = {k: int(raw[k]) for k in raw}
    for k in sorted(raw, key=lambda k: raw[k] - quotas[k], reverse=True)[: total - sum(quotas.values())]:
        quotas[k] += 1
    return quotas


def matches(row: dict, cond: dict) -> bool:
    return all(row.get(k) in set(map(str, v)) for k, v in (cond or {}).items())


def violated_rules(row: dict, rules: list[dict]) -> list[str]:
    hits = []
    for rule in rules:
        if matches(row, rule.get("when")):
            if any(row.get(k) in set(map(str, v)) for k, v in (rule.get("forbid") or {}).items()):
                hits.append(rule["name"])
    return hits


def apply_overrides(row: dict, overrides: list[dict]) -> list[str]:
    applied = []
    for o in overrides:
        if matches(row, o.get("when")):
            for k, v in (o.get("set") or {}).items():
                if row.get(k) != v:
                    row[k] = str(v)
                    applied.append(o["name"])
    return applied


def dist(rows: list[dict], key: str, top: int | None = None) -> dict:
    c = collections.Counter(r.get(key) for r in rows)
    n = sum(c.values()) or 1
    items = c.most_common(top) if top else sorted(c.items(), key=lambda kv: str(kv[0]))
    return {str(k): round(100 * v / n, 1) for k, v in items}


def interleaved_cycle(shares: dict) -> list[str]:
    """100-slot label cycle proportional to `shares`; every prefix is as close to the target
    shares as possible (largest-deficit-first), so short runs are not skewed to rare labels."""
    quotas = largest_remainder({str(k): float(v) for k, v in shares.items()}, 100)
    assigned: collections.Counter = collections.Counter()
    order: list[str] = []
    for i in range(1, 101):
        lab = max(quotas, key=lambda k: (quotas[k] * i / 100 - assigned[k], quotas[k]))
        order.append(lab)
        assigned[lab] += 1
    return order


def load_overlays(cfg: dict) -> list[dict]:
    """`overlay:` (single, legacy) or `overlays:` (list). Each has id, label, and one of:
    `value` (constant), `shares` (global balanced rotation), or `shares_by` + nested `shares`
    keyed by the parent field's value (balanced rotation within each parent value)."""
    raw = cfg.get("overlays") or ([cfg["overlay"]] if cfg.get("overlay") else [])
    out = []
    for o in raw:
        item = {"id": o["id"], "label": o.get("label", o["id"])}
        if "value" in o:
            item["values"] = [str(o["value"])]
            item["cycle"] = [str(o["value"])]
        elif o.get("shares_by"):
            item["shares_by"] = o["shares_by"]
            item["cycles"] = {str(parent): interleaved_cycle(sh) for parent, sh in o["shares"].items()}
            item["values"] = sorted({v for sh in o["shares"].values() for v in map(str, sh)})
        else:
            item["cycle"] = interleaved_cycle(o["shares"])
            item["values"] = list(map(str, o["shares"]))
        out.append(item)
    return out


def stamp_overlays(rows: list[dict], overlays: list[dict]) -> None:
    """Stamp in list order so a `shares_by` overlay can depend on an earlier one. `rows` is in
    cell order, so a global rotation is balanced overall and near-balanced within cells."""
    for o in overlays:
        if "shares_by" in o:
            ptr: collections.Counter = collections.Counter()
            for r in rows:
                parent = str(r.get(o["shares_by"]))
                if parent not in o["cycles"]:
                    raise SystemExit(f"overlay {o['id']}: no shares for {o['shares_by']}={parent!r}")
                cyc = o["cycles"][parent]
                r[o["id"]] = cyc[ptr[parent] % len(cyc)]
                ptr[parent] += 1
        else:
            for i, r in enumerate(rows):
                r[o["id"]] = o["cycle"][i % len(o["cycle"])]


# --- main ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="pool dir (default: persona/datasets/%s-<name>)" % POOL_PREFIX)
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    seed = int(cfg.get("seed", 42))
    total = int(cfg["total"])
    pinned = {k: str(v) for k, v in (cfg.get("pinned") or {}).items()}
    cells_cfg = cfg["cells"] if isinstance(cfg["cells"], list) else [cfg["cells"]]
    cell_dims = [c["dimension"] for c in cells_cfg]
    filters = {k: [str(x) for x in v] for k, v in (cfg.get("filters") or {}).items()}
    rules = cfg.get("coherence_rules") or []
    overrides = cfg.get("overrides") or []
    drop_dims = [str(d) for d in (cfg.get("drop_dimensions") or [])]
    overlays = load_overlays(cfg)
    draws = int(cfg.get("draws_per_cell", 40000))
    max_draws = int(cfg.get("max_draws_per_cell", draws))
    out_dir = (args.out or (REPO_ROOT / "persona" / "datasets" / f"{POOL_PREFIX}-{cfg['name']}")).resolve()
    if not out_dir.is_relative_to(REPO_ROOT):
        raise SystemExit(f"--out must be inside the repo ({REPO_ROOT}); the Playground only lists pools there")

    # cartesian cells over every cell dimension; joint share = product of shares
    combos = list(itertools.product(*[[(str(v), float(s)) for v, s in c["shares"].items()] for c in cells_cfg]))
    joint = {tuple(v for v, _ in combo): math.prod(s for _, s in combo) for combo in combos}
    quotas = largest_remainder(joint, total)

    print(f"[plan] total={total} pinned={pinned} cells={cell_dims} ({len(quotas)} cells) draws/cell={draws} (max {max_draws}) seed={seed}")
    sampler = _dag_sampler(seed=seed)

    kept_all: list[dict] = []
    stats: dict[str, dict] = {}
    rule_hits: collections.Counter = collections.Counter()
    override_hits: collections.Counter = collections.Counter()
    t0 = time.time()
    for cell_values, quota in quotas.items():
        if quota == 0:
            continue
        label = " × ".join(cell_values)
        fixed = dict(pinned, **dict(zip(cell_dims, cell_values)))
        t = time.time()
        drawn = n_filt = 0
        ok: list[dict] = []
        while len(ok) < quota and drawn < max_draws:  # top up weak cells instead of failing
            rows = [{k: str(v) for k, v in r.items()} for r in sampler.sample(draws, fixed=fixed)]
            drawn += draws
            filt = [r for r in rows if matches(r, filters)]
            n_filt += len(filt)
            for r in filt:
                v = violated_rules(r, rules)
                if v:
                    rule_hits.update(v)
                else:
                    ok.append(r)
        if len(ok) < quota:
            raise SystemExit(
                f"cell {label}: only {len(ok)} coherent matches for quota {quota} after {drawn} draws; "
                f"raise max_draws_per_cell (now {max_draws}) or loosen filters"
            )
        chosen = ok[:quota]
        for r in chosen:
            for d in drop_dims:
                r.pop(d, None)
        kept_all.extend(chosen)
        stats[label] = {
            "draws": drawn, "after_filters": n_filt, "after_rules": len(ok), "quota": quota,
            "yield_pct": round(100 * len(ok) / drawn, 2), "seconds": round(time.time() - t, 1),
        }
        print(f"  {label:<52} drew {drawn:>6} → filters {n_filt:>5} → coherent {len(ok):>5} → took {quota:>4}  ({stats[label]['seconds']}s)")

    stamp_overlays(kept_all, overlays)
    for r in kept_all:  # after overlays, so an override may key on an overlay value
        override_hits.update(apply_overrides(r, overrides))

    # --- write pool (wipe stale files from a previous build of the same pool) --
    if out_dir.exists():
        for f in out_dir.glob("persona_*.yaml"):
            f.unlink()
    personas = [
        _persona_entry(persona_id=f"{i:04d}", dimensions=row, version=DEFAULT_PERSONA_VERSION)
        for i, row in enumerate(kept_all, start=1)
    ]
    overlay_dims = [{"id": o["id"], "label": o["label"], "values": o["values"]} for o in overlays] or None
    cfg_rel = str(args.config.resolve().relative_to(REPO_ROOT)) if args.config.resolve().is_relative_to(REPO_ROOT) else str(args.config)
    manifest = write_persona_dataset(
        out_dir=out_dir, personas=personas, repo_root=REPO_ROOT, kind=cfg["name"], seed=seed,
        smoke_persona_id="0001", overlay_dimensions=overlay_dims,
        manifest_name=cfg.get("display_name"), manifest_description=cfg.get("description"),
        extra_manifest={
            "cohort_config": cfg_rel, "cohort_recipe": "pin-early/filter-late",
            "pinned": pinned, "cell_dimensions": cell_dims,
            "cell_quotas": {" × ".join(k): v for k, v in quotas.items()},
            "filters": filters, "coherence_rules": [r["name"] for r in rules],
            "overrides": [o["name"] for o in overrides], "dropped_dimensions": drop_dims,
            "overlay_ids": [o["id"] for o in overlays], "cell_stats": stats, "rule_rejections": dict(rule_hits), "override_applications": dict(override_hits),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    dn = cfg.get("display_names")
    if dn:  # config-driven names: deterministic by id, unique within the cohort
        import hashlib
        used: set[str] = set(); names = {}
        for p in personas:
            pid, dims = p["persona_id"], p["dimensions"]
            pool = dn["first_names_woman"] if dims.get("gender_identity") == "Woman" else dn["first_names_man"]
            for probe in range(1000):
                h = int(hashlib.sha256(f"{pid}:{probe}".encode()).hexdigest()[:12], 16)
                cand = f"{pool[h % len(pool)]} {dn['last_names'][(h // len(pool)) % len(dn['last_names'])]}"
                if cand not in used:
                    break
            used.add(cand); names[pid] = cand
    else:
        names = assign_cohort_display_names([(p["persona_id"], p["dimensions"]) for p in personas])
    for p in personas:
        path = out_dir / f"persona_{p['persona_id']}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["display_name"] = names[p["persona_id"]]
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    mpath = out_dir / "manifest.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    for row in m["personas"]:
        row["display_name"] = names[row["persona_id"]]
    mpath.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- validation report -----------------------------------------------------
    L = [f"# Cohort validation — {cfg['name']}", "",
         f"{len(kept_all)} personas · seed {seed} · built {time.strftime('%Y-%m-%d %H:%M')} · {round(time.time()-t0)}s · config `{cfg_rel}`", "",
         "## Target vs built (cell dimensions)", ""]
    for c in cells_cfg:
        d = c["dimension"]
        tgt = {str(k): round(100 * float(v) / sum(map(float, c["shares"].values())), 1) for k, v in c["shares"].items()}
        built = dist(kept_all, d)
        L += [f"| {d} | target % | built % | n |", "|---|---|---|---|"]
        L += [f"| {k} | {tgt[k]} | {built.get(k, 0)} | {sum(1 for r in kept_all if r.get(d) == k)} |" for k in tgt]
        L.append("")
    if overlays:
        L += ["## Overlay dimensions (stamped after sampling)", ""]
        for o in overlays:
            if "shares_by" in o:
                L += [f"### `{o['id']}` by `{o['shares_by']}`", ""]
                for parent in sorted(o["cycles"]):
                    sub = [r for r in kept_all if str(r.get(o["shares_by"])) == parent]
                    L.append(f"- {parent} (n={len(sub)}): {dist(sub, o['id'])}")
                L.append("")
            else:
                L += [f"- `{o['id']}`: {dist(kept_all, o['id'])}"]
        first = overlays[0]
        L += ["", f"### `{first['id']}` × `{cell_dims[0]}` (should be flat)", ""]
        for k in dist(kept_all, cell_dims[0]):
            L.append(f"- {k}: {dist([r for r in kept_all if r.get(cell_dims[0]) == k], first['id'])}")
    L += ["", "## Pinned / filtered dimensions (all should be 100 % inside the allowed set)", ""]
    for k, v in list(pinned.items()) + [(k, ",".join(v)) for k, v in filters.items()]:
        L.append(f"- `{k}` = {v}: built {dist(kept_all, k)}")
    L += ["", "## Coherence", "", f"Rule rejections during sampling: {dict(rule_hits) or 'none'}",
          f"Overrides applied: {dict(override_hits) or 'none'} · dropped dimensions: {drop_dims or 'none'}", "",
          "Residual check on the built pool:", ""]
    for name in [r["name"] for r in rules]:
        L.append(f"- {name}: {sum(1 for r in kept_all if name in violated_rules(r, rules))}")
    L += ["", "## Un-pinned dimensions — sanity (compare against the 1M reference slice)", ""]
    for k in ("years_experience", "life_stage", "gender_identity", "company_size", "socioeconomic_band",
              "multilingualism", "english_proficiency", "economic_motivation", "risk_tolerance", "tech_savviness"):
        L.append(f"- `{k}`: {dist(kept_all, k, top=8)}")
    L += ["", "## Sampling stats per cell", "", "| cell | draws | after filters | coherent | quota | yield % |", "|---|---|---|---|---|---|"]
    for k, s in stats.items():
        L.append(f"| {k} | {s['draws']} | {s['after_filters']} | {s['after_rules']} | {s['quota']} | {s['yield_pct']} |")
    (out_dir / "validation.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"[done] wrote {manifest['count']} personas → {out_dir.relative_to(REPO_ROOT)}  (+ manifest.json, validation.md)")
    print(f"[done] {round(time.time()-t0)}s; rule rejections {dict(rule_hits) or 'none'}; overrides {dict(override_hits) or 'none'}")


if __name__ == "__main__":
    main()
