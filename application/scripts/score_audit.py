#!/usr/bin/env python3
"""Post-hoc scoring pass for page-audit v2 trials (design spec §7).

Why this exists: ratings given at the end of a long browsing trajectory lose the
persona (ablation/findings/trust-rating-collapse.md) - `trust` comes back 3 for
everyone. Re-scoring outside the browse, with the persona text and the persona's own
notes close together, restores the variation. This script does exactly that for each
finished trial of a job:

  system  = the persona system text the trial itself saw (same template, same YAML)
  user    = page brief + the persona's self-briefing + its observation notes from the
            visit + the eight scale anchors, verbatim from the task instruction
  never   = the in-browse scores, the decision fields, the improvement fields

and writes the eight re-derived scores back as `<dim>_scored` facets in
verifier/structured_output.json (so the Playground report charts them next to the
in-browse ones), as `scores_post_hoc` in verifier/quality.json (for
ablation/summarize_run.py), and the full exchange in verifier/post_hoc_scoring.json.

    python application/scripts/score_audit.py jobs/<job-dir> [--workers 3] [--limit N]
                                              [--force] [--dry-run] [--model gpt-5.6-luna]

Needs OPENAI_BASE_URL / OPENAI_API_KEY (read from application/playground/.env.local when
not already in the environment).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for extra in (REPO / "environment" / "agents", REPO / "src"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from matraix.agents.persona.loader import load_persona  # noqa: E402
from matraix.agents.persona.templating import (  # noqa: E402
    PERSONA_SYSTEM_TEMPLATE,
    render_persona_template,
    resolve_persona_template,
)

SCORED_VERSION = "post-hoc-1.0"
DIMS = ["understanding", "language_relevance", "practical_value", "trust", "next_step_confidence", "next_step_ease"]
FOLLOW_UPS = ["cta_match", "contact_likelihood"]
ALL_SCORES = DIMS + FOLLOW_UPS
# Where each scored facet lives in structured_output.json, and its label.
FACET_HOME = {**{k: "page_audit" for k in DIMS}, "cta_match": "cta_followthrough", "contact_likelihood": "decision"}
LABELS = {
    "understanding": "Understanding (1-5, scored after the visit)",
    "language_relevance": "Language and relevance (1-5, scored after the visit)",
    "practical_value": "Perceived practical value (1-5, scored after the visit)",
    "trust": "Trust (1-5, scored after the visit)",
    "next_step_confidence": "Confidence in the next step (1-5, scored after the visit)",
    "next_step_ease": "Ease of completing the next step (1-5, scored after the visit)",
    "cta_match": "What followed the button matched expectation (1-5, scored after the visit)",
    "contact_likelihood": "Likelihood of contacting within a week (1-5, scored after the visit)",
}
# The persona's observations - what it saw and quoted - in the order they were made.
OBSERVATION_FIELDS = [
    ("first_screen_takeaway", "What you took from the first screen"),
    ("would_continue", "Would you keep reading"),
    ("would_continue_reason", "Why"),
    ("what_it_does", "What the company does, as you understood it"),
    ("problems_recognised", "Problems of yours you recognised on the page"),
    ("language_felt_familiar", "Wording that felt like your world (quoted)"),
    ("language_felt_off", "Wording that felt off or foreign (quoted)"),
    ("claims_credible", "Claims you found credible (quoted)"),
    ("claims_need_proof", "Claims you would want proof for (quoted)"),
    ("confusing_or_missing", "What was confusing, missing, unconvincing or irrelevant"),
    ("strongest_element", "Strongest part of the page"),
    ("weakest_element", "Weakest part of the page"),
    ("hesitate_or_leave_reason", "What would make you hesitate or leave"),
    ("primary_cta_seen", "The primary button you found"),
    ("cta_expectation", "What you expected it to lead to"),
    ("cta_inspected", "Did you click it"),
    ("cta_reality", "What actually followed"),
    ("form_asks_for", "What the form asked for"),
    ("missing_info", "Information you missed"),
]
# The scorer must not see these: they carry the in-browse verdict.
WITHHELD = set(ALL_SCORES) | {"next_step", "basis_primary", "trust_action", "reason", "improvement_suggestion", "improvement_check", "retain"}

_print_lock = threading.Lock()


def log(msg: str) -> None:
    with _print_lock:
        print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- inputs

def load_env_file(path: Path) -> None:
    """Fill OPENAI_* from a KEY=VALUE file when the shell did not export them."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def section(text: str, heading: str) -> str:
    """The body of a `## heading` section up to the next `## `."""
    m = re.search(rf"^## {re.escape(heading)}\s*$", text, re.M)
    if not m:
        raise ValueError(f"section '{heading}' not found")
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start() if nxt else None].strip()


def task_dir_of(job: Path) -> Path:
    cfg = json.loads((job / "config.json").read_text())
    rel = (cfg.get("datasets") or cfg.get("tasks") or [{}])[0].get("path") or ""
    for base in (REPO, Path.cwd()):
        cand = (base / rel).resolve()
        if (cand / "instruction.md").is_file():
            return cand
    raise FileNotFoundError(f"task dir for {job.name}: {rel}")


def persona_system_text(persona_path: str) -> str:
    p = Path(persona_path)
    if not p.is_file():
        # persona_meta paths are absolute into the tree the backend ran from; fall back to the repo copy.
        marker = "persona/datasets/"
        if marker in persona_path:
            p = REPO / persona_path[persona_path.index(marker):]
    persona = load_persona(p)
    return render_persona_template(resolve_persona_template(persona, None, PERSONA_SYSTEM_TEMPLATE), persona)


def fmt_value(v) -> str:
    if v is None or v == "" or v == []:
        return "(none)"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, list):
        parts = []
        for item in v:
            if isinstance(item, dict):
                parts.append("- " + "; ".join(f"{k}: {item[k]}" for k in ("what", "where", "kind") if k in item))
            else:
                parts.append(f"- {item}")
        return "\n".join(parts)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def build_user_message(audit: dict, page_brief: str, anchors: str) -> str:
    early = bool(audit.get("left_early"))
    lines = [
        "Earlier today you visited one page of a supplier's website, as yourself, and wrote notes while reading.",
        "Below are the page brief you were given, the briefing you wrote before opening the page, and your notes.",
        "Now, away from the browser, rate the page on the scales below from your own situation - your job, your",
        "responsibilities, what you came for today, how pressing it is - using only what you actually observed.",
        "Use the whole range. 3 means genuinely middling, not a polite default. Do not be polite to the supplier.",
        "",
        "# Page brief",
        page_brief,
        "",
        "# Your briefing before opening the page",
        f"- Why you came today: {fmt_value(audit.get('arrived_with'))}",
        f"- In your own words: {fmt_value(audit.get('self_briefing'))}",
        "",
        "# Your notes from the visit" + (" (you left after the first screen)" if early else ""),
    ]
    for key, title in OBSERVATION_FIELDS:
        if key in WITHHELD:
            continue
        val = audit.get(key)
        if early and key not in ("first_screen_takeaway", "would_continue", "would_continue_reason"):
            continue
        if val in (None, "", [], "unknown"):
            continue
        body = fmt_value(val)
        lines.append(f"**{title}:**" + ("\n" + body if "\n" in body else " " + body))
    lines += ["", "# The 1-5 scales", anchors, ""]
    if early:
        lines += [
            "You left after the first screen, so rate only `understanding` and `contact_likelihood`;",
            "give every other scale the value \"unknown\".",
        ]
    else:
        lines += [
            "If you did not click the button, give `next_step_ease` and `cta_match` the value \"unknown\".",
        ]
    lines += [
        "",
        "Answer with a single JSON object and nothing else, with exactly these keys, each holding",
        '{"score": <integer 1-5 or "unknown">, "why": "<one sentence, from your situation>"}:',
        ", ".join(ALL_SCORES),
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- model

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()


def call_anthropic(model: str, system: str, user: str, retries: int = 6) -> tuple[dict, dict]:
    """The Copilot passthrough gateway speaks Anthropic's /v1/messages and nothing else,
    so scoring a Claude run with the same model does not go through the OpenAI client."""
    import urllib.request

    base = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
    body = {"model": model, "max_tokens": 1500, "system": system, "messages": [{"role": "user", "content": user}]}
    delay = 3.0
    last: Exception | None = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(
                f"{base}/v1/messages", method="POST", data=json.dumps(body).encode("utf-8"),
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
                         "content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            text = "".join(part.get("text", "") for part in payload.get("content") or [] if part.get("type") == "text")
            usage = payload.get("usage") or {}
            return json.loads(_strip_fences(text)), {"prompt_tokens": usage.get("input_tokens"),
                                                     "completion_tokens": usage.get("output_tokens")}
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise RuntimeError(f"anthropic call failed after {retries} attempts: {last!r}")


def call_model(client, model: str, system: str, user: str, retries: int = 6) -> tuple[dict, dict]:
    delay = 3.0
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={"type": "json_object"},
                max_completion_tokens=1200,
            )
            text = resp.choices[0].message.content or ""
            usage = {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens}
            return json.loads(text), usage
        except json.JSONDecodeError as exc:
            last = exc
        except Exception as exc:  # rate limits, transient 5xx, timeouts
            last = exc
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise RuntimeError(f"model call failed after {retries} attempts: {last!r}")


def normalise(raw: dict) -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    for key in ALL_SCORES:
        item = raw.get(key)
        score = item.get("score") if isinstance(item, dict) else item
        if isinstance(score, bool):
            score = "unknown"
        if isinstance(score, (int, float)) and 1 <= score <= 5:
            out[key] = int(round(score))
        elif isinstance(score, str) and score.strip().isdigit() and 1 <= int(score) <= 5:
            out[key] = int(score)
        else:
            out[key] = "unknown"
    return out


# --------------------------------------------------------------------------- outputs

def atomic_write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    os.replace(tmp, path)


def write_back(trial: Path, scores: dict, whys: dict, meta: dict) -> None:
    ver = trial / "verifier"
    so_path = ver / "structured_output.json"
    so = json.loads(so_path.read_text())
    by_type = {c.get("contextType"): c for c in so.get("contexts") or [] if isinstance(c, dict)}
    for key, value in scores.items():
        ctx = by_type.get(FACET_HOME[key])
        if ctx is None:
            continue
        facets = ctx.setdefault("facets", [])
        facets[:] = [f for f in facets if f.get("key") != f"{key}_scored"]
        if value == "unknown":
            facets.append({"key": f"{key}_scored", "label": LABELS[key], "role": "score", "kind": "categorical", "value": "unknown"})
        else:
            facets.append({"key": f"{key}_scored", "label": LABELS[key], "role": "score", "kind": "numerical", "value": value,
                           "scaleMin": 1, "scaleMax": 5})
    so.setdefault("postHocScoring", {}).update(meta)
    atomic_write(so_path, so)

    q_path = ver / "quality.json"
    if q_path.is_file():
        q = json.loads(q_path.read_text())
        q["scores_post_hoc"] = scores
        q["post_hoc"] = meta
        atomic_write(q_path, q)

    atomic_write(ver / "post_hoc_scoring.json", {**meta, "scores": scores, "why": whys})


# --------------------------------------------------------------------------- driver

def scoreable(trial: Path, force: bool, only_segment: str | None = None) -> bool:
    ver = trial / "verifier"
    if not (ver / "structured_output.json").is_file():
        return False
    if not (trial / "artifacts" / "app" / "output" / "page_audit.json").is_file():
        return False
    if only_segment:
        q = ver / "quality.json"
        if not q.is_file():
            return False
        try:
            seg = str((json.loads(q.read_text()).get("persona") or {}).get("traffic_segment") or "")
        except Exception:  # noqa: BLE001
            return False
        # Match on the slug or the label's leading words ("prospect" vs "Prospect (…)").
        if only_segment.lower() not in seg.lower().replace(" ", "_"):
            return False
    return force or not (ver / "post_hoc_scoring.json").is_file()


def load_audit(trial: Path) -> dict:
    """The persona's artifact, with the same repairs the verifier applies."""
    raw = trial / "artifacts" / "app" / "output" / "page_audit.json"
    try:
        return json.loads(raw.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        pass
    # Reuse the verifier's lenient loader from the task's tests dir.
    import importlib.util

    tests = task_dir_of(trial.parent) / "tests" / "test_state.py"
    os.environ.setdefault("AUDIT_OUTPUT", str(raw))
    os.environ.setdefault("AUDIT_INPUT_DIR", str(tests.parent.parent / "input"))
    os.environ.setdefault("HARBOR_VERIFIER_DIR", str(trial / "verifier"))
    spec = importlib.util.spec_from_file_location("audit_verifier", tests)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    data, _health = mod._load_json_lenient(raw)
    return data


def score_trial(client, model: str, trial: Path, page_brief: str, anchors: str, dry_run: bool) -> str:
    audit = load_audit(trial)
    meta_persona = json.loads((trial / "persona_meta.json").read_text())
    system = persona_system_text(meta_persona["persona_path"])
    user = build_user_message(audit, page_brief, anchors)
    prompt_hash = hashlib.sha256((system + "\n\n" + user).encode("utf-8")).hexdigest()[:16]
    if dry_run:
        print(f"===== {trial.name} · system {len(system)} chars · user {len(user)} chars · sha {prompt_hash}\n")
        print(user)
        return "dry-run"
    if model.startswith("claude") or model.startswith("anthropic/"):
        raw, usage = call_anthropic(model.split("/")[-1], system, user)
    else:
        raw, usage = call_model(client, model, system, user)
    scores = normalise(raw)
    whys = {k: (raw.get(k) or {}).get("why") if isinstance(raw.get(k), dict) else None for k in ALL_SCORES}
    meta = {
        "version": SCORED_VERSION,
        "model": model,
        "scored_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "prompt_sha256_16": prompt_hash,
        "persona_path": meta_persona["persona_path"],
        "left_early": bool(audit.get("left_early")),
        "usage": usage,
    }
    write_back(trial, scores, whys, meta)
    return " ".join(f"{k[:5]}={scores[k]}" for k in ALL_SCORES)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", type=Path)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="score at most N trials (0 = all)")
    ap.add_argument("--force", action="store_true", help="re-score trials that already have post_hoc_scoring.json")
    ap.add_argument("--only-segment", default=None,
                    help="score only this traffic segment (e.g. prospect). The six dimensions are "
                         "reported for prospects only, so scoring the rest buys nothing.")
    ap.add_argument("--dry-run", action="store_true", help="print the user message for the first trial and exit")
    ap.add_argument("--env-file", type=Path, default=REPO / "application" / "playground" / ".env.local")
    a = ap.parse_args()

    load_env_file(a.env_file)
    task = task_dir_of(a.job)
    instruction = (task / "instruction.md").read_text(encoding="utf-8")
    page_brief = section(instruction, "Page brief")
    anchors = section(instruction, "The 1–5 scales")

    trials = sorted(p for p in a.job.iterdir() if p.is_dir() and scoreable(p, a.force, a.only_segment))
    if a.limit:
        trials = trials[: a.limit]
    if not trials:
        log("nothing to score")
        return 0
    if a.dry_run:
        score_trial(None, a.model, trials[0], page_brief, anchors, True)
        return 0

    client = None
    if not (a.model.startswith("claude") or a.model.startswith("anthropic/")):
        import openai

        client = openai.OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"], timeout=120)
    log(f"scoring {len(trials)} trials of {a.job.name} with {a.model}, {a.workers} workers")
    done = 0
    failed: list[str] = []
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(score_trial, client, a.model, t, page_brief, anchors, False): t for t in trials}
        for fut in concurrent.futures.as_completed(futs):
            trial = futs[fut]
            try:
                summary = fut.result()
                done += 1
                if done % 25 == 0 or done == len(trials):
                    log(f"  {done}/{len(trials)} scored ({time.time() - t0:.0f}s) · last: {trial.name[-7:]} {summary}")
            except Exception as exc:
                failed.append(trial.name)
                log(f"  FAILED {trial.name}: {exc}")
    log(f"done: {done} scored, {len(failed)} failed" + (f": {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
