#!/usr/bin/env python3
"""Generate one job recipe per page for the Infobric page-audit task.

`generate_application_job.py` does not expose harbor's `extra_instruction_paths`,
which is how one task serves many pages. This wraps it: generate a recipe per
page brief, then inject the brief path and the parallelism.

    uv run python application/scripts/make_page_jobs.py --per-tier 30
    uv run python application/scripts/make_page_jobs.py --per-tier 1 --pages homepage --name-prefix pilot
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TASK = "application/tasks/web_infobric-page-audit"
POOL = "persona/datasets/generated-persona-dev-infobric-managers-1000"
RECIPE_DIR = REPO / "configs/jobs/application-task-job-recipe"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", nargs="*", default=["homepage", "pricing", "tier_page"])
    ap.add_argument("--per-tier", type=int, default=30, help="personas per tier per page")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", default="anthropic/claude-haiku-4.5")
    ap.add_argument("--parallel", type=int, default=5)
    ap.add_argument("--name-prefix", default="infobric")
    args = ap.parse_args()

    for page in args.pages:
        brief = Path(TASK) / "pages" / f"{page}.md"
        if not (REPO / brief).is_file():
            sys.exit(f"no page brief at {brief}")
        name = f"{args.name_prefix}-{page.replace('_', '-')}"
        cmd = [
            "uv", "run", "python", "application/scripts/generate_application_job.py",
            "--task", TASK, "--dataset", POOL, "--no-strategy",
            "--stratify", "tier", "--stratified-allocation", "perCell",
            "--sample-size-per-value-group", str(args.per_tier),
            "--seed", str(args.seed), "--model-name", args.model, "--name", name,
        ]
        out = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        if out.returncode != 0:
            sys.exit(f"generate failed for {page}:\n{out.stdout}\n{out.stderr}")
        selected = next((l for l in out.stdout.splitlines() if "Matched" in l), "")

        recipe = RECIPE_DIR / f"{name}.yaml"
        text = recipe.read_text(encoding="utf-8")
        text = text.replace("n_concurrent_trials: 1", f"n_concurrent_trials: {args.parallel}")
        # harbor reads these files and folds them into the agent's instruction
        text = text.replace(
            "tasks:\n",
            f"extra_instruction_paths:\n- {brief.as_posix()}\ntasks:\n",
        )
        recipe.write_text(text, encoding="utf-8")
        print(f"{name:<28} {selected}  brief={brief.name}  parallel={args.parallel}")
        print(f"  uv run matraix run -c configs/jobs/application-task-job-recipe/{name}.yaml")


if __name__ == "__main__":
    main()
