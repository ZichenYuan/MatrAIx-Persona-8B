"""Verifier — Infobric free first visit.

Validity gate only. The persona starts on the homepage, browses freely within a
step budget, ends with a decision, and files a short questionnaire plus a
self-reported journey (the pages it opened, in order).

The journey here is what the persona *says* it did. The objective record is the
agent's own action log (trial `agent/browser_use.txt` / `trajectory.json`), which
lives outside the container; comparing the two is an analysis step, not a
verifier step. What this verifier can check is internal consistency: the journey
starts at the start URL, the exit page is the last page listed, and the
reached_pricing / reached_contact flags agree with the URLs listed.

Everything the persona wrote is surfaced as structured facets so reporting.json
and `matraix results --group-by <dimension>` can aggregate it.
Facet contract: application/task-spec/web/README.md § "Required Facets For
`decision`" plus the recommended `decision_process` context for browsing tasks.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

OUTPUT = Path("/app/output/free_visit.json")

START_PATH = "/se"                     # https://infobric.com/se/
PRICING_FRAGMENTS = ("/pris",)         # /se/pris-och-paketering/
CONTACT_FRAGMENTS = ("/kontakt", "demo", "/prova", "/testa", "trial", "contact", "boka")

MISSING_INFO = {
    "price", "integrations", "hardware", "setup_time", "references", "data_privacy", "contract_terms",
}
NEXT_STEPS = {"contact_sales", "book_demo", "try_free", "learn_more", "come_back_later", "leave"}
BASIS_PRIMARY = {
    # Construction-procurement reasons; every option available to every tier so
    # which tier picks which is the finding, not the design.
    "legal_compliance", "consolidation", "price", "integrations", "ease_of_rollout",
    "proof_references", "support", "features", "fit", "other",
}
STOPPED_BECAUSE = {"found_enough", "ran_out_of_steps", "could_not_find", "lost_interest"}
FOUND = {"yes", "partly", "no"}
TRUST_ACTION = {"share_data_now", "need_references_first", "need_pilot_first", "would_not_proceed"}
CONVERTING = {"contact_sales", "book_demo", "try_free"}

# Near-miss enum values models produce; unambiguous, so map rather than discard.
_ALIASES = {
    "hardware_requirements": "hardware", "hardware_details": "hardware",
    "pricing": "price", "prices": "price", "cost": "price", "costs": "price",
    "integration": "integrations", "setup": "setup_time",
    "implementation_time": "setup_time", "onboarding_time": "setup_time",
    "privacy": "data_privacy", "gdpr": "data_privacy",
    "contract": "contract_terms", "terms": "contract_terms",
    "customer_references": "references", "reference_customers": "references",
    "found_what_i_needed": "found_enough", "done": "found_enough", "enough": "found_enough",
    "out_of_steps": "ran_out_of_steps", "budget": "ran_out_of_steps",
    "not_found": "could_not_find", "gave_up": "could_not_find",
    "bored": "lost_interest", "not_relevant": "lost_interest",
    "partially": "partly", "partial": "partly",
    "references_first": "need_references_first", "need_references": "need_references_first",
    "pilot_first": "need_pilot_first", "need_pilot": "need_pilot_first", "trial_first": "need_pilot_first",
    "share_now": "share_data_now", "proceed_now": "share_data_now",
    "would_not": "would_not_proceed", "no": "would_not_proceed",
}


def _verifier_dir() -> Path:
    explicit = os.environ.get("HARBOR_VERIFIER_DIR")
    if explicit:
        path = Path(explicit)
        path.mkdir(parents=True, exist_ok=True)
        return path
    container_default = Path("/logs/verifier")
    container_default.mkdir(parents=True, exist_ok=True)
    return container_default


def _rating(data: dict, key: str) -> int:
    value = data.get(key)
    assert isinstance(value, (int, float)), f"{key} must be numeric"
    value = int(round(float(value)))
    assert 1 <= value <= 7, f"{key} must be between 1 and 7"
    return value


def _string(data: dict, key: str, max_len: int = 2000) -> str:
    value = data.get(key)
    assert isinstance(value, str) and value.strip(), f"{key} must be a non-empty string"
    return value.strip()[:max_len]


def _bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    assert token in {"true", "false", "yes", "no"}, f"{key} must be true or false"
    return token in {"true", "yes"}


def _canon(raw: object, allowed: set[str]) -> str | None:
    token = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    for candidate in (
        token,
        _ALIASES.get(token),
        token[:-1] if token.endswith("s") else None,
        token.split("_", 1)[-1] if "_" in token else None,
    ):
        if candidate and candidate in allowed:
            return candidate
        if candidate and _ALIASES.get(candidate) in allowed:
            return _ALIASES[candidate]
    return None


def _subset(data: dict, key: str, allowed: set[str], unmapped: list[str]) -> list[str]:
    value = data.get(key)
    assert isinstance(value, list), f"{key} must be a list"
    out: list[str] = []
    for item in value:
        canon = _canon(item, allowed)
        if canon is None:
            unmapped.append(f"{key}:{item}")
        elif canon not in out:
            out.append(canon)
    return out


def _path(url: str) -> str:
    """Site-relative path, normalised: no scheme/host, no query/fragment, no
    trailing slash or stray dot (models emit 'https://infobric.com/se/.')."""
    u = re.sub(r"^https?://[^/]+", "", str(url).strip())
    u = u.split("#", 1)[0].split("?", 1)[0].rstrip("/.")
    return u or "/"


def _section(path: str) -> str:
    """First path segment under /se/, e.g. 'pris-och-paketering'; 'home' for /se."""
    rest = path[len(START_PATH):].strip("/") if path.startswith(START_PATH) else path.strip("/")
    return rest.split("/", 1)[0] if rest else "home"


def _facet(key: str, label: str, role: str, kind: str, value, explains: str | None = None) -> dict:
    out = {"key": key, "label": label, "role": role, "kind": kind, "value": value}
    if explains:
        out["explainsFacetKey"] = explains
    return out


def test_output_exists() -> None:
    assert OUTPUT.is_file(), f"Missing {OUTPUT}"


def _load_output() -> tuple[dict, str]:
    """Parse the questionnaire. Some models emit invalid \\x escapes for Swedish
    characters; retry leniently so one bad escape does not discard a trial, and
    record that it happened."""
    raw = OUTPUT.read_text()
    try:
        return json.loads(raw), "clean"
    except json.JSONDecodeError:
        return json.loads(raw, strict=False), "repaired_control_chars"


def test_output_schema() -> None:
    data, json_health = _load_output()
    assert isinstance(data, dict), "root must be an object"
    unmapped: list[str] = []

    # --- journey (self-reported) ---------------------------------------------
    start_url = _string(data, "start_url")
    assert "infobric.com" in start_url, f"start_url should be on infobric.com, got {start_url!r}"
    pages = data.get("pages_visited")
    assert isinstance(pages, list) and pages, "pages_visited must be a non-empty list"
    assert all(isinstance(p, str) and p.strip() for p in pages), "pages_visited entries must be URLs"
    paths: list[str] = []
    for p in pages:                     # collapse consecutive duplicates
        q = _path(p)
        if not paths or paths[-1] != q:
            paths.append(q)
    assert paths[0] == START_PATH, f"the first page visited must be the start page, got {pages[0]!r}"
    on_site = [("infobric.com" in p.lower()) for p in pages]
    left_site = not all(on_site)

    exit_page = _string(data, "exit_page")
    exit_path = _path(exit_page)
    journey_consistent = exit_path == paths[-1]
    if not journey_consistent:
        unmapped.append(f"exit_page:{exit_page} (last visited was {paths[-1]})")
        exit_path = paths[-1]

    reached_pricing = _bool(data, "reached_pricing")
    reached_contact = _bool(data, "reached_contact")
    # Derive from the raw URLs, fragment included: a product page's "#price"
    # anchor counts as reaching pricing even though _path() strips it.
    raw_urls = [str(p).lower() for p in pages]
    derived_pricing = any(any(f in u for f in PRICING_FRAGMENTS) or "price" in u for u in raw_urls)
    derived_contact = any(any(f in u for f in CONTACT_FRAGMENTS) for u in raw_urls)

    steps_used = data.get("steps_used")
    assert isinstance(steps_used, (int, float)), "steps_used must be numeric"
    steps_used = int(round(float(steps_used)))
    assert 1 <= steps_used <= 200, "steps_used out of range"

    stopped = _canon(data.get("stopped_because"), STOPPED_BECAUSE)
    assert stopped, f"stopped_because must be one of {sorted(STOPPED_BECAUSE)}, got {data.get('stopped_because')!r}"
    found = _canon(data.get("found_what_needed"), FOUND)
    assert found, f"found_what_needed must be one of {sorted(FOUND)}, got {data.get('found_what_needed')!r}"
    obstacle = _string(data, "biggest_obstacle")
    conclusion = _string(data, "conclusion")

    # --- questionnaire --------------------------------------------------------
    clarity = _rating(data, "clarity")
    trust = _rating(data, "trust")
    contact_likelihood = _rating(data, "contact_likelihood")
    trust_action = _canon(data.get("trust_action"), TRUST_ACTION)
    assert trust_action, f"trust_action must be one of {sorted(TRUST_ACTION)}, got {data.get('trust_action')!r}"
    missing = _subset(data, "missing_info", MISSING_INFO, unmapped)
    next_step = _canon(data.get("next_step"), NEXT_STEPS)
    assert next_step, f"next_step must be one of {sorted(NEXT_STEPS)}, got {data.get('next_step')!r}"
    basis = _canon(data.get("basis_primary"), BASIS_PRIMARY) or "other"
    improvement = _string(data, "improvement_suggestion")
    reason = _string(data, "reason")

    contexts = [
        {
            "key": "decision.primary",
            "label": "Next step after the visit",
            "contextType": "decision",
            "facets": [
                _facet("decision_outcome", "Decision outcome", "primary", "categorical", next_step),
                _facet("basis_primary", "Primary basis", "primary", "categorical", basis),
                _facet("reason", "Reason", "explanation", "textual", reason, explains="decision_outcome"),
                _facet("decision_subject_label", "Site", "evidence", "categorical", "Infobric website (free visit)"),
                _facet("decision_subject_id", "Site id", "evidence", "categorical", "infobric_site"),
                _facet("contact_likelihood", "Likelihood of contacting (1-7)", "score", "numerical",
                       contact_likelihood),
                _facet("converted", "Would engage sales", "primary", "categorical",
                       "true" if next_step in CONVERTING else "false"),
                _facet("trust_action", "Needed before going further", "primary", "categorical", trust_action),
            ],
        },
        {
            # The journey. contextType follows the task-spec's recommended
            # `decision_process` context for tasks where the persona browses.
            "key": "journey.primary",
            "label": "The visit",
            "contextType": "decision_process",
            "facets": [
                _facet("pages_visited_count", "Pages opened", "score", "numerical", len(paths)),
                _facet("options_considered_count", "Distinct pages", "score", "numerical", len(set(paths))),
                _facet("steps_used", "Actions used (self-reported)", "score", "numerical", steps_used),
                _facet("exit_page", "Exit page", "primary", "categorical", exit_path),
                _facet("exit_section", "Exit section", "primary", "categorical", _section(exit_path)),
                _facet("reached_pricing", "Reached pricing (self-reported)", "evidence", "categorical",
                       "true" if reached_pricing else "false"),
                _facet("reached_contact", "Reached contact/demo/trial (self-reported)", "evidence", "categorical",
                       "true" if reached_contact else "false"),
                _facet("reached_pricing_by_url", "Reached pricing (from URLs listed)", "evidence", "categorical",
                       "true" if derived_pricing else "false"),
                _facet("reached_contact_by_url", "Reached contact (from URLs listed)", "evidence", "categorical",
                       "true" if derived_contact else "false"),
                _facet("left_site", "Left infobric.com", "evidence", "categorical",
                       "true" if left_site else "false"),
                _facet("journey_consistent", "Exit page matches last page listed", "evidence", "categorical",
                       "true" if journey_consistent else "false"),
                _facet("stopped_because", "Why the visit ended", "primary", "categorical", stopped),
                _facet("found_what_needed", "Found what was needed", "primary", "categorical", found),
                _facet("pages_visited", "Pages visited, in order", "evidence", "textual", " -> ".join(paths)),
                _facet("comparison_notes", "Biggest obstacle", "explanation", "textual", obstacle),
            ],
        },
        {
            "key": "visit_feedback.primary",
            "label": "After the visit",
            "contextType": "visit_feedback",
            "facets": [
                _facet("clarity", "Clarity: what it would do for me (1-7)", "score", "numerical", clarity),
                _facet("trust", "Trust: would rely on them (1-7)", "score", "numerical", trust),
                _facet("conclusion", "Conclusion", "evidence", "textual", conclusion),
                _facet("missing_info", "Missing info", "evidence", "categorical",
                       ", ".join(missing) or "nothing"),
                _facet("unmapped_values", "Values needing canonicalisation", "evidence", "categorical",
                       ", ".join(unmapped) or "none"),
                _facet("json_health", "Artifact JSON health", "evidence", "categorical", json_health),
            ],
        },
        {
            # What to change, in the persona's own words — the partner-facing payload.
            "key": "site_improvement.primary",
            "label": "How to improve the site",
            "contextType": "site_improvement",
            "facets": [
                _facet("improvement_suggestion", "Suggested change", "explanation", "textual", improvement),
                _facet("biggest_obstacle", "Biggest obstacle", "evidence", "textual", obstacle),
            ],
        },
        {
            "key": "task_outcome.primary",
            "label": "Task outcome",
            "contextType": "task_outcome",
            "facets": [
                _facet("outcome_status", "Outcome status", "primary", "categorical", "passed"),
                _facet("goal_completion_ratio", "Goal completion ratio", "score", "numerical", 1.0),
                _facet("primary_failure_reason", "Primary failure reason", "primary", "categorical", "none"),
                _facet("outcome_explanation", "Outcome explanation", "explanation", "textual",
                       f"The persona visited {len(paths)} page(s), ended on {exit_path}, "
                       f"chose {next_step}, and saved a valid {OUTPUT.name}."),
            ],
        },
    ]

    (_verifier_dir() / "structured_output.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "artifactType": "matraix.trial_evaluation",
                "taskType": "web",
                "presenceCheck": {"passed": True, "requiredArtifacts": [OUTPUT.name], "missingArtifacts": []},
                "sourceArtifacts": {"taskOutput": str(OUTPUT)},
                "contexts": contexts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
