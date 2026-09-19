#!/usr/bin/env python3
"""Re-run the current verifier on trials that finished without a crash but were
scored 0 - typically an audit the older verifier could not parse before a JSON
repair was added. The verifier is deterministic given the artifact, so this is the
same check the container would have run, with today's tests/test_state.py.

For each such trial: run pytest on the task's test_state.py with the trial's
artifact, the task's inventory, and the trial's own persona file; if it passes,
rewrite verifier/{reward.txt,structured_output.json,quality.json,ctrf.json}, set
result.json verifier_result.rewards.reward = 1.0 and record `reverified`. The
original result.json is kept as result.json.before-reverify.

    python application/scripts/reverify_audit.py jobs/<job-dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


_CTRF: dict[str, bool] = {}


def has_ctrf_plugin(python: str) -> bool:
    if python not in _CTRF:
        _CTRF[python] = subprocess.run([python, "-c", "import pytest_json_ctrf"], capture_output=True).returncode == 0
    return _CTRF[python]


def task_dir_of(job: Path) -> Path:
    cfg = json.loads((job / "config.json").read_text())
    rel = (cfg.get("datasets") or cfg.get("tasks") or [{}])[0].get("path") or ""
    cand = (REPO / rel).resolve()
    if not (cand / "tests" / "test_state.py").is_file():
        raise FileNotFoundError(f"task dir for {job.name}: {rel}")
    return cand


def candidates(job: Path) -> list[Path]:
    out = []
    for res in sorted(job.glob("*/result.json")):
        try:
            r = json.loads(res.read_text())
        except json.JSONDecodeError:
            continue
        if not r.get("finished_at") or r.get("exception_info"):
            continue
        reward = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        if reward == 1.0:
            continue
        if (res.parent / "artifacts" / "app" / "output" / "page_audit.json").is_file():
            out.append(res.parent)
    return out


def persona_file(trial: Path) -> Path | None:
    meta = trial / "persona_meta.json"
    if not meta.is_file():
        return None
    raw = json.loads(meta.read_text()).get("persona_path") or ""
    p = Path(raw)
    if p.is_file():
        return p
    marker = "persona/datasets/"
    if marker in raw:
        alt = REPO / raw[raw.index(marker):]
        if alt.is_file():
            return alt
    return None


def reverify(trial: Path, task: Path, python: str, dry_run: bool) -> tuple[bool, str]:
    artifact = trial / "artifacts" / "app" / "output" / "page_audit.json"
    persona = persona_file(trial)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_in = Path(tmp) / "input"
        shutil.copytree(task / "input", tmp_in)
        if persona is not None:
            shutil.copyfile(persona, tmp_in / "persona.yaml")
        ver = Path(tmp) / "verifier"
        ver.mkdir()
        env = dict(os.environ, AUDIT_OUTPUT=str(artifact), AUDIT_INPUT_DIR=str(tmp_in), HARBOR_VERIFIER_DIR=str(ver))
        ctrf = ["--ctrf", str(ver / "ctrf.json")] if has_ctrf_plugin(python) else []
        p = subprocess.run([python, "-m", "pytest", "-q", "-rA", *ctrf, str(task / "tests" / "test_state.py")],
                           env=env, capture_output=True, text=True, cwd=str(tmp))
        passed = p.returncode == 0 and (ver / "structured_output.json").is_file()
        summary = [ln for ln in p.stdout.splitlines() if ln.startswith(("PASSED", "FAILED", "ERROR"))]
        if dry_run or not passed:
            return passed, "; ".join(summary)[:300] or p.stdout[-300:]
        # write back
        vdir = trial / "verifier"
        vdir.mkdir(exist_ok=True)
        for name in ("structured_output.json", "quality.json", "ctrf.json"):
            if (ver / name).is_file():
                shutil.copyfile(ver / name, vdir / name)
        (vdir / "reward.txt").write_text("1\n")
        (vdir / "test-stdout.txt").write_text(p.stdout)
        res_path = trial / "result.json"
        backup = trial / "result.json.before-reverify"
        if not backup.exists():
            shutil.copyfile(res_path, backup)
        r = json.loads(res_path.read_text())
        r.setdefault("verifier_result", {}).setdefault("rewards", {})["reward"] = 1.0
        r["reverified"] = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "by": "application/scripts/reverify_audit.py",
                           "previous_reward": ((json.loads(backup.read_text()).get("verifier_result") or {}).get("rewards") or {}).get("reward")}
        res_path.write_text(json.dumps(r, indent=2))
        return True, "; ".join(summary)[:300]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    job = a.job.resolve()
    task = task_dir_of(job)
    trials = candidates(job)
    print(f"{len(trials)} candidate trial(s) in {job.name} (finished, no crash, reward != 1)", file=sys.stderr)
    fixed = 0
    for t in trials:
        ok, msg = reverify(t, task, a.python, a.dry_run)
        fixed += ok
        print(f"  {t.name[-7:]}: {'PASS' if ok else 'still failing'} - {msg}", file=sys.stderr)
    print(f"{'would pass' if a.dry_run else 'reverified'}: {fixed} of {len(trials)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
