#!/usr/bin/env python3
"""Derive an ablation pool that keeps only the display name and chosen fields (default: tier).

    uv run python persona/scripts/strip_cohort.py \
        persona/datasets/generated-persona-dev-infobric-managers-v2-1000 \
        persona/datasets/generated-persona-dev-infobric-managers-v0-1000 --keep tier

Persona ids, display names and the kept fields are copied 1:1 from the source pool, so a
trial on persona 0042 in v0 is the same person as 0042 in the source with everything
else removed. `manifest.json` lists only the kept fields as overlay dimensions.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
for entry in (REPO_ROOT, REPO_ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from matraix.persona_generator import write_persona_dataset  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("dest", type=Path)
    ap.add_argument("--keep", nargs="+", default=["tier"], help="dimension ids to keep (default: tier)")
    ap.add_argument("--name", default=None, help="manifest kind (default: <source kind>-stripped)")
    args = ap.parse_args()

    src_manifest = json.loads((args.source / "manifest.json").read_text(encoding="utf-8"))
    overlay_by_id = {o["id"]: o for o in src_manifest.get("overlay_dimensions") or []}
    personas, names = [], {}
    for path in sorted(args.source.glob("persona_*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        dims = data["dimensions"]
        missing = [k for k in args.keep if k not in dims]
        if missing:
            raise SystemExit(f"{path.name}: missing {missing}")
        personas.append({
            "persona_id": data["persona_id"], "version": data.get("version", "1.0"),
            "source": data.get("source", "synthetic"), "dimensions": {k: dims[k] for k in args.keep},
        })
        names[data["persona_id"]] = data.get("display_name", "")

    overlay = [overlay_by_id.get(k) or {"id": k, "label": k, "values": sorted({p["dimensions"][k] for p in personas})}
               for k in args.keep]
    if args.dest.exists():
        for f in args.dest.glob("persona_*.yaml"):
            f.unlink()
    kind = args.name or f"{src_manifest.get('kind', args.source.name)}-stripped"
    write_persona_dataset(
        out_dir=args.dest, personas=personas, repo_root=REPO_ROOT, kind=kind,
        seed=int(src_manifest.get("seed", 0)), smoke_persona_id=personas[0]["persona_id"],
        overlay_dimensions=overlay,
        manifest_name=f"{src_manifest.get('name', kind)} — {'+'.join(args.keep)} only",
        manifest_description=f"Ablation pool: display name + {', '.join(args.keep)} copied from {args.source.name}; all other dimensions removed.",
        extra_manifest={
            "stripped_from": str(args.source.relative_to(REPO_ROOT)) if args.source.is_relative_to(REPO_ROOT) else str(args.source),
            "kept_dimensions": args.keep,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    for p in personas:
        path = args.dest / f"persona_{p['persona_id']}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["display_name"] = names[p["persona_id"]]
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    mpath = args.dest / "manifest.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    for row in m["personas"]:
        row["display_name"] = names[row["persona_id"]]
    mpath.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[done] {len(personas)} personas → {args.dest} keeping {args.keep}")


if __name__ == "__main__":
    main()
