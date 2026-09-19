#!/usr/bin/env python3
"""Build a synthetic persona cohort from a YAML config: pin early DAG nodes, draw,
filter late nodes, enforce coherence rules, fill per-cell quotas (drawing more for weak
cells up to `max_draws_per_cell`), stamp overlays, derive rule-based fields, apply
overrides, and write a Playground-visible pool (one YAML per persona + manifest.json)
plus a validation.md report.

    uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_managers.yaml
    uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_managers_v2.yaml
    uv run python persona/scripts/build_cohort.py persona/scripts/cohort_configs/infobric_pilot_full.yaml

Why not `generate_dev_personas.py --filter …`? Pinning a node only conditions the
nodes sampled AFTER it. Pinning late nodes (seniority, years_experience) leaves age
drawn from the general prior — toddler CEOs. This script pins early nodes (as
cells with shares, so quotas are exact) and rejection-filters late ones, which
keeps the joint coherent. See PLAN.md §4.

Config features (all optional except `name`, `total`, `cells`):

- `groups:` — sub-populations with their own share of `total`, their own `filters`
  (merged over the top-level ones; a null value removes a filter), their own `cells`,
  and constant `stamp:` fields. Managers and staff need different seniority filters and
  age shares; one global filter list cannot express that. No `groups` = one group.
- `cells[].shares_by:` — a cell's shares may depend on an earlier cell dimension
  (gender split that differs by domain). Use `"*"` as the fallback parent.
- `overlays[].shares_by:` — a field name or a list of field names; the share table is
  keyed by the parent values joined with " | ". Any component may be `"*"`. The value
  `~omit` means "leave this field out for this persona".
- `overlay_assignment: shuffled` — exact quotas per parent key, assigned in a seeded
  random order, so two overlays are independent of each other. The default `rotation`
  keeps the v1 / v2 behaviour (a fixed 100-slot cycle), which ties every rotation
  overlay to the same row index.
- `derived:` — rule-based fields: first rule whose `when` matches sets `value`, else
  `default`. `stage: before_overlays` lets an overlay depend on a derived field.
- Field ids that start with `_` are build-time helpers; they are removed before writing.
- `on_shortfall: borrow` — a cell that cannot fill its quota takes coherent surplus
  personas from the closest cells of the same group instead of aborting the build.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import random
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
OMIT = "~omit"
SEP = " | "


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


def stable_seed(*parts: object) -> int:
    """Seed that does not change between Python runs (the built-in hash() is salted)."""
    return int(hashlib.sha256("::".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def cell_quotas(cells_cfg: list[dict], total: int) -> tuple[list[str], dict]:
    """Cartesian cells. A cell's shares may depend on an earlier cell via `shares_by`."""
    dims = [c["dimension"] for c in cells_cfg]
    joint: dict[tuple, float] = {}

    def rec(i: int, vals: list[str], share: float) -> None:
        if i == len(cells_cfg):
            joint[tuple(vals)] = share
            return
        c = cells_cfg[i]
        table = c["shares"]
        if c.get("shares_by"):
            parent = vals[dims.index(c["shares_by"])]
            table = table.get(parent, table.get("*"))
            if table is None:
                raise SystemExit(f"cell {c['dimension']}: no shares for {c['shares_by']}={parent!r}")
        s = float(sum(table.values()))
        for v, sh in table.items():
            if float(sh) > 0:
                rec(i + 1, vals + [str(v)], share * float(sh) / s)

    rec(0, [], 1.0)
    return dims, largest_remainder(joint, total)


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
    `value` (constant), `shares` (global), or `shares_by` (field or list of fields) + nested
    `shares` keyed by the parent values joined with " | " ("*" = any)."""
    raw = cfg.get("overlays") or ([cfg["overlay"]] if cfg.get("overlay") else [])
    out = []
    for o in raw:
        item = {"id": o["id"], "label": o.get("label", o["id"])}
        if "value" in o:
            item["tables"] = {(): {str(o["value"]): 1.0}}
            item["parents"] = []
        elif o.get("shares_by"):
            parents = o["shares_by"] if isinstance(o["shares_by"], list) else [o["shares_by"]]
            item["parents"] = [str(p) for p in parents]
            item["tables"] = {}
            for key, sh in o["shares"].items():
                parts = tuple(p.strip() for p in str(key).split("|"))
                if len(parts) != len(parents):
                    raise SystemExit(f"overlay {o['id']}: key {key!r} needs {len(parents)} parts ({parents})")
                item["tables"][parts] = {str(k): float(v) for k, v in sh.items()}
        else:
            item["parents"] = []
            item["tables"] = {(): {str(k): float(v) for k, v in o["shares"].items()}}
        item["values"] = sorted({v for t in item["tables"].values() for v in t if v != OMIT})
        out.append(item)
    return out


def lookup_table(o: dict, row: dict) -> tuple[tuple, dict]:
    """Share table for this row: exact parent key first, then keys with more "*" parts."""
    actual = tuple(str(row.get(p)) for p in o["parents"])
    n = len(actual)
    for wild in range(n + 1):
        for idx in itertools.combinations(range(n), wild):
            cand = tuple("*" if i in idx else actual[i] for i in range(n))
            if cand in o["tables"]:
                return actual, o["tables"][cand]
    raise SystemExit(f"overlay {o['id']}: no shares for {dict(zip(o['parents'], actual))}")


def stamp_overlay(rows: list[dict], o: dict, mode: str, seed: int) -> None:
    by_parent: dict[tuple, list[dict]] = collections.defaultdict(list)
    tables: dict[tuple, dict] = {}
    for r in rows:
        actual, table = lookup_table(o, r)
        by_parent[actual].append(r)
        tables[actual] = table
    for actual, members in by_parent.items():
        table = tables[actual]
        if mode == "shuffled":  # exact quotas, seeded random order: independent across overlays
            quotas = largest_remainder(table, len(members))
            labels = [lab for lab, q in quotas.items() for _ in range(q)]
            random.Random(stable_seed(seed, o["id"], *actual)).shuffle(labels)
        else:  # legacy rotation (v1 / v2)
            cyc = interleaved_cycle(table)
            labels = [cyc[i % len(cyc)] for i in range(len(members))]
        for r, lab in zip(members, labels):
            if lab != OMIT:
                r[o["id"]] = lab


def apply_derived(rows: list[dict], derived: list[dict], stage: str) -> None:
    for d in derived:
        if d.get("stage", "after_overlays") != stage:
            continue
        for r in rows:
            for rule in d.get("rules") or []:
                if matches(r, rule.get("when")):
                    value = rule["value"]
                    break
            else:
                if "default" not in d:
                    raise SystemExit(f"derived {d['id']}: no rule matched and no default")
                value = d["default"]
            if str(value) != OMIT:
                r[d["id"]] = str(value)


def derived_values(d: dict) -> list[str]:
    vals = [str(r["value"]) for r in d.get("rules") or []] + ([str(d["default"])] if "default" in d else [])
    return sorted({v for v in vals if v != OMIT})


# --- main ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="pool dir (default: persona/datasets/%s-<name>)" % POOL_PREFIX)
    ap.add_argument("--total", type=int, default=None, help="override `total` (small trial builds)")
    args = ap.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    seed = int(cfg.get("seed", 42))
    total = int(args.total or cfg["total"])
    pinned = {k: str(v) for k, v in (cfg.get("pinned") or {}).items()}
    top_cells = cfg["cells"] if isinstance(cfg["cells"], list) else [cfg["cells"]]
    top_filters = {k: [str(x) for x in v] for k, v in (cfg.get("filters") or {}).items()}
    rules = cfg.get("coherence_rules") or []
    overrides = cfg.get("overrides") or []
    derived = cfg.get("derived") or []
    drop_dims = [str(d) for d in (cfg.get("drop_dimensions") or [])]
    overlays = load_overlays(cfg)
    assign_mode = str(cfg.get("overlay_assignment", "rotation"))
    on_shortfall = str(cfg.get("on_shortfall", "fail"))
    draws = int(cfg.get("draws_per_cell", 40000))
    max_draws = int(cfg.get("max_draws_per_cell", draws))
    out_dir = (args.out or (REPO_ROOT / "persona" / "datasets" / f"{POOL_PREFIX}-{cfg['name']}")).resolve()
    if not out_dir.is_relative_to(REPO_ROOT):
        raise SystemExit(f"--out must be inside the repo ({REPO_ROOT}); the Playground only lists pools there")

    groups_cfg = cfg.get("groups") or [{"name": "all", "share": 1}]
    group_totals = largest_remainder({g["name"]: float(g.get("share", 1)) for g in groups_cfg}, total)
    print(f"[plan] total={total} groups={group_totals} pinned={pinned} draws/batch={draws} (max {max_draws}/cell) "
          f"seed={seed} overlays={assign_mode} shortfall={on_shortfall}")
    sampler = _dag_sampler(seed=seed)

    kept_all: list[dict] = []
    stats: dict[str, dict] = {}
    group_report: list[dict] = []
    rule_hits: collections.Counter = collections.Counter()
    override_hits: collections.Counter = collections.Counter()
    t0 = time.time()

    for g in groups_cfg:
        gname, gtotal = g["name"], group_totals[g["name"]]
        if gtotal == 0:
            continue
        g_filters = dict(top_filters)
        for k, v in (g.get("filters") or {}).items():
            if v is None:
                g_filters.pop(k, None)
            else:
                g_filters[k] = [str(x) for x in v]
        g_cells = g.get("cells") or top_cells
        g_stamp = {k: str(v) for k, v in (g.get("stamp") or {}).items()}
        g_draws = int(g.get("draws_per_cell", draws))
        cell_dims, quotas = cell_quotas(g_cells, gtotal)
        print(f"[group] {gname}: {gtotal} personas, {sum(1 for q in quotas.values() if q)} cells over {cell_dims}")

        chosen_by_cell: dict[tuple, list[dict]] = {}
        surplus: list[tuple[tuple, dict]] = []
        short: dict[tuple, int] = {}
        for cell_values, quota in quotas.items():
            if quota == 0:
                continue
            label = f"{gname} · " + " × ".join(cell_values)
            fixed = dict(pinned, **dict(zip(cell_dims, cell_values)))
            t = time.time()
            drawn = n_filt = 0
            ok: list[dict] = []
            while len(ok) < quota and drawn < max_draws:  # top up weak cells instead of failing
                rows = [{k: str(v) for k, v in r.items()} for r in sampler.sample(g_draws, fixed=fixed)]
                drawn += g_draws
                for r in rows:
                    r.update(g_stamp)  # before filters and rules, so both may key on a stamp
                filt = [r for r in rows if matches(r, g_filters)]
                n_filt += len(filt)
                for r in filt:
                    v = violated_rules(r, rules)
                    if v:
                        rule_hits.update(v)
                    else:
                        ok.append(r)
            if len(ok) < quota:
                if on_shortfall != "borrow":
                    raise SystemExit(
                        f"cell {label}: only {len(ok)} coherent matches for quota {quota} after {drawn} draws; "
                        f"raise max_draws_per_cell (now {max_draws}), loosen filters, or set on_shortfall: borrow"
                    )
                short[cell_values] = quota - len(ok)
            chosen_by_cell[cell_values] = ok[:quota]
            surplus.extend((cell_values, r) for r in ok[quota: quota * 3 + 6])
            stats[label] = {
                "draws": drawn, "after_filters": n_filt, "after_rules": len(ok), "quota": quota,
                "yield_pct": round(100 * len(ok) / drawn, 3), "seconds": round(time.time() - t, 1),
            }
            flag = f"  SHORT by {quota - len(ok)}" if len(ok) < quota else ""
            print(f"  {label:<78} drew {drawn:>7} → filters {n_filt:>5} → coherent {len(ok):>5} → took {min(quota, len(ok)):>3}  ({stats[label]['seconds']}s){flag}")

        borrowed = 0
        for cell_values, need in short.items():
            # Closest surplus first. The first cell dimension (age, by convention the one with
            # a hard requirement) outweighs all the others, so borrowing never moves its shares
            # unless no donor with the same value exists.
            surplus.sort(key=lambda cr: -sum((100 if i == 0 else 1) * (a == b) for i, (a, b) in enumerate(zip(cr[0], cell_values))))
            take, surplus = surplus[:need], surplus[need:]
            if len(take) < need:
                raise SystemExit(f"group {gname}: cell {cell_values} short by {need} and only {len(take)} surplus personas to borrow")
            chosen_by_cell[cell_values].extend(r for _, r in take)
            stats[f"{gname} · " + " × ".join(cell_values)]["borrowed"] = need
            borrowed += need
        g_rows = [r for cv in quotas if cv in chosen_by_cell for r in chosen_by_cell[cv]]
        for r in g_rows:
            for d in drop_dims:
                r.pop(d, None)
        kept_all.extend(g_rows)
        group_report.append({"name": gname, "total": gtotal, "cells": g_cells, "cell_dims": cell_dims,
                             "filters": g_filters, "stamp": g_stamp, "borrowed": borrowed, "rows": g_rows})

    apply_derived(kept_all, derived, "before_overlays")
    for o in overlays:  # in list order, so an overlay may depend on an earlier one
        stamp_overlay(kept_all, o, assign_mode, seed)
    apply_derived(kept_all, derived, "after_overlays")
    for r in kept_all:  # after overlays and derived fields, so an override may key on either
        override_hits.update(apply_overrides(r, overrides))
    report_rows = [dict(r) for r in kept_all]  # keeps `_helper` fields for the report only
    for r in kept_all:
        for k in [k for k in r if k.startswith("_")]:
            r.pop(k)

    # --- write pool (wipe stale files from a previous build of the same pool) --
    if out_dir.exists():
        for f in out_dir.glob("persona_*.yaml"):
            f.unlink()
    personas = [
        _persona_entry(persona_id=f"{i:04d}", dimensions=row, version=DEFAULT_PERSONA_VERSION)
        for i, row in enumerate(kept_all, start=1)
    ]
    stamp_values: dict[str, set] = collections.defaultdict(set)
    for g in group_report:
        for k, v in g["stamp"].items():
            if not k.startswith("_"):
                stamp_values[k].add(v)
    stamp_labels = cfg.get("stamp_labels") or {}
    overlay_dims = (
        [{"id": k, "label": stamp_labels.get(k, k), "values": sorted(v)} for k, v in stamp_values.items()]
        + [{"id": o["id"], "label": o["label"], "values": o["values"]} for o in overlays if not o["id"].startswith("_")]
        + [{"id": d["id"], "label": d.get("label", d["id"]), "values": derived_values(d)} for d in derived if not d["id"].startswith("_")]
    ) or None
    cfg_rel = str(args.config.resolve().relative_to(REPO_ROOT)) if args.config.resolve().is_relative_to(REPO_ROOT) else str(args.config)
    manifest = write_persona_dataset(
        out_dir=out_dir, personas=personas, repo_root=REPO_ROOT, kind=cfg["name"], seed=seed,
        smoke_persona_id="0001", overlay_dimensions=overlay_dims,
        manifest_name=cfg.get("display_name"), manifest_description=cfg.get("description"),
        extra_manifest={
            "cohort_config": cfg_rel, "cohort_recipe": "pin-early/filter-late",
            "pinned": pinned,
            "groups": [{"name": g["name"], "total": g["total"], "cell_dimensions": g["cell_dims"],
                        "filters": g["filters"], "stamp": g["stamp"], "borrowed": g["borrowed"]} for g in group_report],
            "coherence_rules": [r["name"] for r in rules],
            "overrides": [o["name"] for o in overrides], "dropped_dimensions": drop_dims,
            "overlay_ids": [o["id"] for o in overlays if not o["id"].startswith("_")],
            "derived_ids": [d["id"] for d in derived if not d["id"].startswith("_")],
            "overlay_assignment": assign_mode,
            "cell_stats": stats, "rule_rejections": dict(rule_hits), "override_applications": dict(override_hits),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    dn = cfg.get("display_names")
    if dn:  # config-driven names: deterministic by id, unique within the cohort
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
    rows_all = report_rows
    L = [f"# Cohort validation — {cfg['name']}", "",
         f"{len(rows_all)} personas · seed {seed} · built {time.strftime('%Y-%m-%d %H:%M')} · {round(time.time()-t0)}s · config `{cfg_rel}`", ""]
    for g in group_report:
        L += [f"## Group `{g['name']}` — {g['total']} personas" + (f" ({g['borrowed']} borrowed from neighbouring cells)" if g["borrowed"] else ""), ""]
        for c in g["cells"]:
            d = c["dimension"]
            if c.get("shares_by"):
                L += [f"`{d}` by `{c['shares_by']}` — built: " + "; ".join(
                    f"{pv}: {dist([r for r in g['rows'] if r.get(c['shares_by']) == pv], d)}"
                    for pv in dist(g["rows"], c["shares_by"])), ""]
                continue
            tgt = {str(k): round(100 * float(v) / sum(map(float, c["shares"].values())), 1) for k, v in c["shares"].items()}
            built = dist(g["rows"], d)
            L += [f"| {d} | target % | built % | n |", "|---|---|---|---|"]
            L += [f"| {k} | {tgt[k]} | {built.get(k, 0)} | {sum(1 for r in g['rows'] if r.get(d) == k)} |" for k in tgt]
            L.append("")
        L += ["Filters (all should be 100 % inside the allowed set):", ""]
        L += [f"- `{k}` = {','.join(v)}: built {dist(g['rows'], k)}" for k, v in g["filters"].items()]
        L.append("")
    if overlays or derived:
        L += ["## Stamped and derived fields", ""]
        for o in overlays:
            if o["parents"]:
                L += [f"### `{o['id']}` by `{' + '.join(o['parents'])}`", ""]
                keys = sorted({tuple(str(r.get(p)) for p in o["parents"]) for r in rows_all})
                for key in keys:
                    sub = [r for r in rows_all if tuple(str(r.get(p)) for p in o["parents"]) == key]
                    L.append(f"- {SEP.join(key)} (n={len(sub)}): {dist(sub, o['id'])}")
                L.append("")
            else:
                L += [f"- `{o['id']}`: {dist(rows_all, o['id'])}", ""]
        for d in derived:
            L += [f"- derived `{d['id']}`: {dist(rows_all, d['id'])}"]
    L += ["", "## Pinned dimensions", ""]
    L += [f"- `{k}` = {v}: built {dist(rows_all, k)}" for k, v in pinned.items()]
    L += ["", "## Coherence", "", f"Rule rejections during sampling: {dict(rule_hits) or 'none'}",
          f"Overrides applied: {dict(override_hits) or 'none'} · dropped dimensions: {drop_dims or 'none'}", "",
          "Residual check on the built pool (after overrides):", ""]
    for name in [r["name"] for r in rules]:
        L.append(f"- {name}: {sum(1 for r in rows_all if name in violated_rules(r, rules))}")
    L += ["", "## Un-pinned dimensions — sanity", ""]
    for k in ("seniority", "role_function", "years_experience", "life_stage", "company_size", "socioeconomic_band",
              "english_proficiency", "tech_savviness", "device_context", "demo_generation", "demo_citizenship_status"):
        L.append(f"- `{k}`: {dist(rows_all, k, top=8)}")
    L += ["", "## Sampling stats per cell", "", "| cell | draws | after filters | coherent | quota | borrowed | yield % |", "|---|---|---|---|---|---|---|"]
    for k, s in stats.items():
        L.append(f"| {k} | {s['draws']} | {s['after_filters']} | {s['after_rules']} | {s['quota']} | {s.get('borrowed', 0)} | {s['yield_pct']} |")
    (out_dir / "validation.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"[done] wrote {manifest['count']} personas → {out_dir.relative_to(REPO_ROOT)}  (+ manifest.json, validation.md)")
    print(f"[done] {round(time.time()-t0)}s; borrowed {sum(g['borrowed'] for g in group_report)}; rule rejections {dict(rule_hits) or 'none'}")


if __name__ == "__main__":
    main()
