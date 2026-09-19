"""Verifier — Infobric page audit v2.

Validity gate plus facet emission for one page of infobric.com, reviewed as a
standalone entry point with a single click on the page's primary next-step button.
Design: docs/superpowers/specs/2026-09-18-infobric-audit-v2-design.md.

Deterministic on purpose: no model calls. Two inputs besides the artifact:

- `/app/input/inventory.json` — the page's hand-checked ground truth (CTA labels and
  target, exact claim strings, which next_step options exist and which count as a
  conversion, a visible-text snapshot). Quoted wording is checked against the snapshot
  so the report can label it "visible on the site" rather than "plausible".
- `/app/input/persona.yaml` — uploaded by the persona agent; used only for fidelity
  checks (does `arrived_with` match the persona's `visit_intent`).

Paths come from the environment so the same code runs on the host in unit tests.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

INSTRUMENT_VERSION = "2.0"

OUTPUT = Path(os.environ.get("AUDIT_OUTPUT", "/app/output/page_audit.json"))
INPUT_DIR = Path(os.environ.get("AUDIT_INPUT_DIR", "/app/input"))
INVENTORY = INPUT_DIR / "inventory.json"
PERSONA = INPUT_DIR / "persona.yaml"
VARIANT_FILE = INPUT_DIR / "variant.txt"

POSITIONS = {"top", "middle", "bottom"}
STOP_POINTS = {"top", "middle", "bottom", "read_all"}
KINDS = {"confusing", "missing", "unconvincing", "irrelevant"}
ARRIVED = {"specific_problem", "exploring"}
YES_NO = {"yes", "no"}
ALL_NEXT_STEPS = {
    "book_demo", "start_trial", "create_free_account", "order_package", "use_calculator",
    "download_guide", "preview_fleet", "contact_sales", "learn_more", "come_back_later", "leave",
}
BASIS_PRIMARY = {
    "legal_compliance", "consolidation", "price", "integrations", "ease_of_rollout",
    "proof_references", "support", "features", "fit", "other",
}
TRUST_ACTION = {"share_data_now", "need_references_first", "need_pilot_first", "would_not_proceed"}
MISSING_INFO = {
    "price", "integrations", "hardware", "setup_time", "references", "data_privacy", "contract_terms",
}
SCORES = ("understanding", "language_relevance", "practical_value", "trust", "next_step_confidence")

# Near-miss enum values; unambiguous, so mapped rather than discarded.
_ALIASES = {
    "problem": "specific_problem", "specific": "specific_problem", "explore": "exploring",
    "browsing": "exploring", "true": "yes", "false": "no",
    "above_the_fold": "top", "hero": "top", "header": "top", "mid": "middle", "footer": "bottom",
    "end": "bottom", "all": "read_all", "everything": "read_all", "whole_page": "read_all",
    "unclear": "confusing", "absent": "missing", "not_convincing": "unconvincing",
    "pricing": "price", "prices": "price", "cost": "price", "integration": "integrations",
    "setup": "setup_time", "privacy": "data_privacy", "gdpr": "data_privacy",
    "contract": "contract_terms", "terms": "contract_terms", "customer_references": "references",
    "demo": "book_demo", "trial": "start_trial", "free_trial": "start_trial",
    "free_account": "create_free_account", "calculator": "use_calculator", "guide": "download_guide",
    "contact": "contact_sales", "contact_us": "contact_sales",
    "references_first": "need_references_first", "pilot_first": "need_pilot_first",
    "share_now": "share_data_now", "would_not": "would_not_proceed",
}


# --------------------------------------------------------------------------- helpers
def _verifier_dir() -> Path:
    explicit = os.environ.get("HARBOR_VERIFIER_DIR")
    path = Path(explicit) if explicit else Path("/logs/verifier")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_json_lenient(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(raw), "clean"
    except json.JSONDecodeError:
        return json.loads(raw, strict=False), "repaired_control_chars"


def _inventory() -> dict:
    if not INVENTORY.is_file():
        return {}
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def _persona_field(key: str) -> str | None:
    if not PERSONA.is_file():
        return None
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", PERSONA.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip().strip("'\"") if match else None


def _canon(raw: object, allowed: set[str]) -> str | None:
    """Map a model-written value onto an enum. Models often append an explanation
    ("specific_problem — I need…", "learn_more: because…"), so the value is also tried
    as the text before the first separator, and finally by keyword."""
    text = str(raw or "").strip().lower()
    head = re.split(r"\s*[—–:;,(]\s*|\s+-\s+|\s{2,}", text, maxsplit=1)[0]
    for piece in (text, head, head.split()[0] if head.split() else ""):
        token = piece.strip().replace(" ", "_").replace("-", "_").strip("_.")
        for candidate in (token, _ALIASES.get(token), token[:-1] if token.endswith("s") else None):
            if candidate and candidate in allowed:
                return candidate
            if candidate and _ALIASES.get(candidate) in allowed:
                return _ALIASES[candidate]
    for keyword, value in _KEYWORDS:
        if keyword in text and value in allowed:
            return value
    return None


# Last-resort keyword mapping, checked in order, only within the allowed set.
_KEYWORDS = (
    ("specific", "specific_problem"), ("problem", "specific_problem"), ("explor", "exploring"),
    ("read_all", "read_all"), ("whole", "read_all"), ("entire", "read_all"),
    ("would not", "would_not_proceed"), ("reference", "need_references_first"), ("pilot", "need_pilot_first"),
    ("trial", "need_pilot_first"), ("share", "share_data_now"),
)


def _string(data: dict, key: str, max_len: int = 3000) -> str:
    value = data.get(key)
    assert isinstance(value, str) and value.strip(), f"{key} must be a non-empty string"
    return value.strip()[:max_len]


def _score(data: dict, key: str, allow_unknown: bool = False) -> int | str:
    value = data.get(key)
    if allow_unknown and (value is None or str(value).strip().lower() == "unknown"):
        return "unknown"
    assert isinstance(value, (int, float)), f"{key} must be a number 1-5"
    value = int(round(float(value)))
    assert 1 <= value <= 5, f"{key} must be between 1 and 5"
    return value


def _str_list(data: dict, key: str, max_items: int = 20) -> list[str]:
    value = data.get(key)
    if value is None:
        return []
    assert isinstance(value, list), f"{key} must be a list"
    return [str(v).strip() for v in value if str(v).strip()][:max_items]


def _enum_list(data: dict, key: str, allowed: set[str], unmapped: list[str]) -> list[str]:
    out: list[str] = []
    for item in _str_list(data, key):
        canon = _canon(item, allowed)
        if canon is None:
            unmapped.append(f"{key}:{item}")
        elif canon not in out:
            out.append(canon)
    return out


def _bool(data: dict, key: str) -> bool:
    value = data.get(key)
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    assert token in {"true", "false", "yes", "no"}, f"{key} must be true or false"
    return token in {"true", "yes"}


def _norm(text: str) -> str:
    text = text.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[\"'«»“”‘’]", "", text)
    return re.sub(r"\s+", " ", text).strip(" .,:;!?-–—")


def _grounded(quote: str, snapshot: str) -> bool:
    """Is the quoted wording actually on the page? Exact after normalisation, else the
    first eight words (models trim long sentences), else a 60-character prefix."""
    q = _norm(quote)
    if len(q) < 6:
        return False
    if q in snapshot:
        return True
    words = q.split()
    if len(words) >= 8 and " ".join(words[:8]) in snapshot:
        return True
    return len(q) >= 60 and q[:60] in snapshot


def _grounding(quotes: list[str], snapshot: str) -> tuple[int, int, list[str]]:
    hits = [q for q in quotes if _grounded(q, snapshot)]
    misses = [q[:80] for q in quotes if q not in hits]
    return len(hits), len(quotes), misses


def _facet(key: str, label: str, role: str, kind: str, value, explains: str | None = None) -> dict:
    out = {"key": key, "label": label, "role": role, "kind": kind, "value": value}
    if explains:
        out["explainsFacetKey"] = explains
    return out


def _join(items: list[str], empty: str = "none") -> str:
    return " | ".join(items) if items else empty


# --------------------------------------------------------------------------- tests
def test_output_exists() -> None:
    assert OUTPUT.is_file(), f"Missing {OUTPUT}"


def test_output_schema() -> None:
    data, json_health = _load_json_lenient(OUTPUT)
    assert isinstance(data, dict), "root must be an object"
    inv = _inventory()
    page_id = str(inv.get("page_id") or "page")
    page_label = str(inv.get("label") or inv.get("url") or page_id)
    snapshot = _norm(str(inv.get("text_snapshot") or ""))
    available = set(inv.get("available_next_steps") or ALL_NEXT_STEPS)
    conversions = set(inv.get("conversion_next_steps") or [])
    cta_labels = [str(inv.get("primary_cta", {}).get("label") or "")] + [
        str(c.get("label") or "") for c in inv.get("secondary_ctas") or []
    ]
    cta_labels = [_norm(c) for c in cta_labels if c]
    cta_fragments = [str(inv.get("primary_cta", {}).get("url_fragment") or "")] + [
        str(c.get("url_fragment") or "") for c in inv.get("secondary_ctas") or []
    ]
    cta_fragments = [f for f in cta_fragments if f]
    unmapped: list[str] = []
    variant = VARIANT_FILE.read_text(encoding="utf-8").strip() if VARIANT_FILE.is_file() else "full"

    # --- A. self-briefing -----------------------------------------------------
    self_briefing = _string(data, "self_briefing")
    intent = (_persona_field("visit_intent") or "").lower()
    persona_arrived = (
        "specific_problem" if "specific problem" in intent
        else "exploring" if "exploring" in intent else None
    )
    arrived = _canon(data.get("arrived_with"), ARRIVED)
    if arrived is None:
        # A fidelity field, not a validity gate: record the miss, do not fail the trial.
        unmapped.append(f"arrived_with:{str(data.get('arrived_with'))[:60]}")
        arrived = persona_arrived or "exploring"
    arrived_matches = "n/a" if persona_arrived is None else ("true" if persona_arrived == arrived else "false")

    # --- B. first screen ------------------------------------------------------
    first_takeaway = _string(data, "first_screen_takeaway")
    first_match = _score(data, "first_screen_expectation_match")
    would_continue = _canon(data.get("would_continue"), YES_NO)
    assert would_continue, "would_continue must be yes or no"
    would_continue_reason = _string(data, "would_continue_reason")

    # --- C. full page ---------------------------------------------------------
    what_it_does = _string(data, "what_it_does")
    problems = _str_list(data, "problems_recognised")
    familiar = _str_list(data, "language_felt_familiar")
    off = _str_list(data, "language_felt_off")
    credible = _str_list(data, "claims_credible")
    need_proof = _str_list(data, "claims_need_proof")
    raw_cm = data.get("confusing_or_missing") or []
    assert isinstance(raw_cm, list), "confusing_or_missing must be a list"
    confusing: list[dict] = []
    for item in raw_cm[:20]:
        if isinstance(item, str):
            item = {"what": item, "where": "unknown", "kind": "confusing"}
        assert isinstance(item, dict) and str(item.get("what", "")).strip(), "confusing_or_missing entries need 'what'"
        kind = _canon(item.get("kind"), KINDS) or "confusing"
        where = _canon(item.get("where"), POSITIONS) or "unknown"
        confusing.append({"what": str(item["what"]).strip()[:300], "where": where, "kind": kind})
    dead = _str_list(data, "dead_click_candidates")
    stop = _canon(data.get("attention_stop_point"), STOP_POINTS)
    assert stop, f"attention_stop_point must be one of {sorted(STOP_POINTS)}"
    strongest = _string(data, "strongest_element")
    strongest_pos = _canon(data.get("strongest_position"), POSITIONS) or "unknown"
    weakest = _string(data, "weakest_element")
    weakest_pos = _canon(data.get("weakest_position"), POSITIONS) or "unknown"
    hesitate = _string(data, "hesitate_or_leave_reason")
    scores = {k: _score(data, k) for k in SCORES}

    # --- D. CTA hop -----------------------------------------------------------
    cta_seen = _string(data, "primary_cta_seen")
    cta_expectation = _string(data, "cta_expectation")
    cta_inspected = _bool(data, "cta_inspected")
    cta_url = str(data.get("cta_page_url") or "unknown").strip()
    cta_reality = str(data.get("cta_reality") or "unknown").strip()[:2000]
    form_asks = _str_list(data, "form_asks_for")
    cta_match = _score(data, "cta_match", allow_unknown=True)
    ease = _score(data, "next_step_ease", allow_unknown=True)
    if not cta_inspected:
        cta_match, ease = "unknown", "unknown"
    cta_label_grounded = "true" if cta_labels and _norm(cta_seen) in cta_labels else (
        "partial" if cta_labels and any(l in _norm(cta_seen) or _norm(cta_seen) in l for l in cta_labels) else "false"
    )
    cta_url_ok = "n/a"
    if cta_inspected and cta_url != "unknown":
        cta_url_ok = "true" if cta_fragments and any(f in cta_url for f in cta_fragments) else "false"

    # --- E. decision ----------------------------------------------------------
    next_step = _canon(data.get("next_step"), ALL_NEXT_STEPS)
    assert next_step, f"next_step must be one of {sorted(ALL_NEXT_STEPS)}, got {data.get('next_step')!r}"
    if next_step not in available:
        unmapped.append(f"next_step:{next_step} (not offered on {page_id})")
        next_step = "learn_more" if next_step not in {"come_back_later", "leave"} else next_step
    basis = _canon(data.get("basis_primary"), BASIS_PRIMARY) or "other"
    trust_action = _canon(data.get("trust_action"), TRUST_ACTION)
    assert trust_action, f"trust_action must be one of {sorted(TRUST_ACTION)}"
    contact = _score(data, "contact_likelihood")
    missing = _enum_list(data, "missing_info", MISSING_INFO, unmapped)
    reason = _string(data, "reason")
    improvement = _string(data, "improvement_suggestion")
    improvement_check = _string(data, "improvement_check")
    retain = _string(data, "retain")

    # --- grounding against the page snapshot ----------------------------------
    c_hit, c_tot, c_miss = _grounding(credible + need_proof, snapshot)
    p_hit, p_tot, p_miss = _grounding(familiar + off, snapshot)

    contexts = [
        {
            "key": "decision.primary",
            "label": "Next step after the page",
            "contextType": "decision",
            "facets": [
                _facet("decision_outcome", "Decision outcome", "primary", "categorical", next_step),
                _facet("basis_primary", "Primary basis", "primary", "categorical", basis),
                _facet("reason", "Reason", "explanation", "textual", reason, explains="decision_outcome"),
                _facet("decision_subject_label", "Page", "evidence", "categorical", page_label),
                _facet("decision_subject_id", "Page id", "evidence", "categorical", page_id),
                _facet("converted", "Took a conversion step on this page", "primary", "categorical",
                       "true" if next_step in conversions else "false"),
                _facet("contact_likelihood", "Likelihood of contacting (1-5)", "score", "numerical", contact),
                _facet("trust_action", "Needed before going further", "primary", "categorical", trust_action),
            ],
        },
        {
            "key": "first_impression.primary",
            "label": "First screen, before scrolling",
            "contextType": "first_impression",
            "facets": [
                _facet("first_screen_expectation_match", "First screen matched expectation (1-5)", "score",
                       "numerical", first_match),
                _facet("would_continue", "Would keep reading after the first screen", "primary", "categorical",
                       would_continue),
                _facet("first_screen_takeaway", "What the first screen said it was", "evidence", "textual",
                       first_takeaway),
                _facet("would_continue_reason", "Why", "explanation", "textual", would_continue_reason,
                       explains="would_continue"),
            ],
        },
        {
            "key": f"page_audit.{page_id}",
            "label": f"Page audit: {page_label}",
            "contextType": "page_audit",
            "facets": [
                _facet("page_id", "Page", "primary", "categorical", page_id),
                _facet("understanding", "Understanding (1-5)", "score", "numerical", scores["understanding"]),
                _facet("language_relevance", "Language and relevance (1-5)", "score", "numerical",
                       scores["language_relevance"]),
                _facet("practical_value", "Perceived practical value (1-5)", "score", "numerical",
                       scores["practical_value"]),
                _facet("trust", "Trust (1-5)", "score", "numerical", scores["trust"]),
                _facet("next_step_confidence", "Confidence in the next step (1-5)", "score", "numerical",
                       scores["next_step_confidence"]),
                _facet("next_step_ease", "Ease of completing the next step (1-5)", "score",
                       "numerical" if ease != "unknown" else "categorical", ease),
                _facet("attention_stop_point", "Where a real visit would stop reading", "primary", "categorical", stop),
                _facet("what_it_does", "What it does, in the persona's words", "evidence", "textual", what_it_does),
                _facet("claims_quoted", "Claims quoted", "score", "numerical", c_tot),
                _facet("claims_grounded", "Claims found on the page", "score", "numerical", c_hit),
                _facet("claims_grounded_share", "Share of quoted claims found on the page", "score", "numerical",
                       round(c_hit / c_tot, 3) if c_tot else 0.0),
                _facet("phrases_quoted", "Phrases quoted", "score", "numerical", p_tot),
                _facet("phrases_grounded", "Phrases found on the page", "score", "numerical", p_hit),
                _facet("ungrounded_quotes", "Quotes not found on the page", "evidence", "textual",
                       _join(c_miss + p_miss)),
                _facet("dead_click_count", "Dead-click candidates named", "score", "numerical", len(dead)),
                _facet("confusing_or_missing_count", "Confusing / missing items named", "score", "numerical",
                       len(confusing)),
                _facet("missing_info", "Missing info", "evidence", "categorical", ", ".join(missing) or "nothing"),
                _facet("unmapped_values", "Values needing canonicalisation", "evidence", "categorical",
                       ", ".join(unmapped) or "none"),
                _facet("json_health", "Artifact JSON health", "evidence", "categorical", json_health),
                _facet("instrument_version", "Instrument version", "evidence", "categorical", INSTRUMENT_VERSION),
                _facet("variant", "Task variant", "evidence", "categorical", variant),
                _facet("device_reviewed", "Device reviewed", "evidence", "categorical", "desktop"),
            ],
        },
        {
            "key": "cta_followthrough.primary",
            "label": "The primary next-step button",
            "contextType": "cta_followthrough",
            "facets": [
                _facet("primary_cta_seen", "Button label seen", "evidence", "categorical", cta_seen[:80]),
                _facet("cta_label_grounded", "Button label is a real CTA on the page", "evidence", "categorical",
                       cta_label_grounded),
                _facet("cta_inspected", "Button was clicked and inspected", "primary", "categorical",
                       "true" if cta_inspected else "false"),
                _facet("cta_url_ok", "Click reached the expected destination", "evidence", "categorical", cta_url_ok),
                _facet("cta_match", "What followed matched expectation (1-5)", "score",
                       "numerical" if cta_match != "unknown" else "categorical", cta_match),
                _facet("cta_expectation", "Expected before clicking", "explanation", "textual", cta_expectation),
                _facet("cta_reality", "What actually followed", "evidence", "textual", cta_reality),
                _facet("form_asks_for", "What the form asks for", "evidence", "textual", _join(form_asks)),
            ],
        },
        {
            "key": f"page_improvement.{page_id}",
            "label": f"How to improve: {page_label}",
            "contextType": "page_improvement",
            "facets": [
                _facet("improvement_suggestion", "Suggested change", "explanation", "textual", improvement),
                _facet("improvement_check", "How to check whether it helped", "explanation", "textual",
                       improvement_check, explains="improvement_suggestion"),
                _facet("retain", "What works and should be kept", "evidence", "textual", retain),
                _facet("strongest_element", "Strongest element", "evidence", "textual",
                       f"[{strongest_pos}] {strongest}"),
                _facet("weakest_element", "Weakest element", "evidence", "textual", f"[{weakest_pos}] {weakest}"),
                _facet("hesitate_or_leave_reason", "What would cause hesitation or leaving", "explanation",
                       "textual", hesitate),
                _facet("problems_recognised", "Own problems recognised on the page", "evidence", "textual",
                       _join(problems)),
                _facet("claims_need_proof", "Claims needing proof (quoted)", "evidence", "textual",
                       _join(need_proof)),
                _facet("claims_credible", "Claims found credible (quoted)", "evidence", "textual", _join(credible)),
                _facet("language_felt_familiar", "Wording that felt familiar (quoted)", "evidence", "textual",
                       _join(familiar)),
                _facet("language_felt_off", "Wording that felt off (quoted)", "evidence", "textual", _join(off)),
                _facet("confusing_or_missing", "Confusing, missing, unconvincing or irrelevant", "evidence", "textual",
                       _join([f"[{c['where']}/{c['kind']}] {c['what']}" for c in confusing])),
                _facet("dead_click_candidates", "Tried to click, nothing happened", "evidence", "textual",
                       _join(dead)),
            ],
        },
        {
            "key": "persona_fidelity.primary",
            "label": "Did the persona come through",
            "contextType": "persona_fidelity",
            "facets": [
                _facet("self_briefing", "Self-briefing", "evidence", "textual", self_briefing),
                _facet("arrived_with", "Reason for the visit (self-reported)", "primary", "categorical", arrived),
                _facet("arrived_with_matches_persona", "Matches the persona's visit_intent", "evidence",
                       "categorical", arrived_matches),
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
                       f"The persona audited {page_label}, "
                       f"{'inspected' if cta_inspected else 'did not inspect'} the primary button, "
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
