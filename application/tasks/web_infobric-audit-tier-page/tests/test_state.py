"""Verifier — Infobric page audit (multi-page).

Validity gate only. The page is chosen per job via `extra_instruction_paths`
(see pages/*.md), so this verifier is page-agnostic: it validates the reported
`page_id` against a registry and checks the URL belongs to that page. For the
tier page it also checks the persona opened the page for its OWN tier, read from
/app/input/persona.yaml (uploaded by the persona agent before the run).

Everything the persona wrote is surfaced as structured facets so
`matraix results --group-by <dimension>` and reporting.json can aggregate it.
Facet contract: application/task-spec/web/README.md § "Required Facets For `decision`".
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

OUTPUT = Path("/app/output/page_audit.json")
PERSONA = Path("/app/input/persona.yaml")

# page_id -> (label, allowed url fragment). One entry per pages/*.md brief.
PAGE_REGISTRY = {
    "homepage": ("Infobric homepage", "infobric.com/se/"),
    "pricing": ("Pricing and packaging", "/pris-och-paketering"),
    "tier_page": ("Audience page", "/vem-vi-hjalper/"),
}
# tier_page only: the persona's own tier decides which URL is correct.
TIER_PAGE = {
    "Main contractor": "huvudentreprenorer",
    "Subcontractor": "underentreprenorer",
    "Developer": "byggherrar",
    "Rental": "uthyrningsforetag",
}

TRUST_SIGNALS = {"logos", "customer_count", "testimonial", "case_studies", "certifications"}
MISSING_INFO = {
    "price", "integrations", "hardware", "setup_time", "references", "data_privacy", "contract_terms",
}
NEXT_STEPS = {"contact_sales", "book_demo", "try_free", "learn_more", "come_back_later", "leave"}
BASIS_PRIMARY = {
    # Construction-procurement reasons, not the e-commerce vocabulary the example
    # tasks use. Every option is available to every tier on purpose: which tier
    # picks which is the finding, so the buckets must not be tier-labelled.
    "legal_compliance", "consolidation", "price", "integrations", "ease_of_rollout",
    "proof_references", "support", "features", "fit", "other",
}
CONVERTING = {"contact_sales", "book_demo", "try_free"}

# Models produce near-misses for these enums ("customer_logos" for "logos"). The
# value is unambiguous, so map it rather than discarding a whole trial. Anything
# still unrecognised is dropped and counted in an `unmapped_values` facet.
_ALIASES = {
    "customer_logos": "logos", "client_logos": "logos", "brand_logos": "logos",
    "customer_testimonial": "testimonial", "testimonials": "testimonial",
    "customer_testimonials": "testimonial", "quotes": "testimonial",
    "customer_stories": "case_studies", "case_study": "case_studies",
    "customer_cases": "case_studies",
    "customers": "customer_count", "user_count": "customer_count",
    "customer_numbers": "customer_count", "certification": "certifications",
    "hardware_requirements": "hardware", "hardware_details": "hardware",
    "pricing": "price", "prices": "price", "cost": "price", "costs": "price",
    "integration": "integrations", "setup": "setup_time",
    "implementation_time": "setup_time", "onboarding_time": "setup_time",
    "privacy": "data_privacy", "gdpr": "data_privacy",
    "contract": "contract_terms", "terms": "contract_terms",
    "customer_references": "references", "reference_customers": "references",
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


def _persona_tier() -> str | None:
    """The persona's own tier, for validating the tier-page choice."""
    if not PERSONA.is_file():
        return None
    match = re.search(r"^\s*tier:\s*(.+?)\s*$", PERSONA.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip().strip("'\"") if match else None


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


def _facet(key: str, label: str, role: str, kind: str, value, explains: str | None = None) -> dict:
    out = {"key": key, "label": label, "role": role, "kind": kind, "value": value}
    if explains:
        out["explainsFacetKey"] = explains
    return out


def test_output_exists() -> None:
    assert OUTPUT.is_file(), f"Missing {OUTPUT}"


def _load_output() -> tuple[dict, str]:
    """Parse the audit. Some models emit invalid \\x escapes for Swedish characters,
    which json.loads rejects outright; retry leniently so one bad escape does not
    discard a whole trial, and record that it happened."""
    raw = OUTPUT.read_text()
    try:
        return json.loads(raw), "clean"
    except json.JSONDecodeError:
        return json.loads(raw, strict=False), "repaired_control_chars"


def test_output_schema() -> None:
    data, json_health = _load_output()
    assert isinstance(data, dict), "root must be an object"

    # --- page identity -------------------------------------------------------
    page_id = _string(data, "page_id").lower()
    assert page_id in PAGE_REGISTRY, f"page_id must be one of {sorted(PAGE_REGISTRY)}, got {page_id!r}"
    page_label, fragment = PAGE_REGISTRY[page_id]
    page_url = _string(data, "page_url")
    assert fragment in page_url, f"page_url {page_url!r} does not look like the {page_id} page ({fragment!r})"

    tier = _persona_tier()
    tier_page_correct = "n/a"
    if page_id == "tier_page":
        assert tier in TIER_PAGE, f"persona tier {tier!r} not recognised; cannot validate tier page"
        expected = TIER_PAGE[tier]
        tier_page_correct = "true" if expected in page_url else "false"
        assert tier_page_correct == "true", (
            f"persona tier is {tier!r} so it should have opened .../{expected}/, got {page_url!r}"
        )
        page_label = f"{page_label}: {tier}"

    # --- ratings and enums ---------------------------------------------------
    summary = _string(data, "one_sentence_summary")
    key_claim = _string(data, "key_claim_noticed")
    clarity = _rating(data, "clarity")
    relevance = _rating(data, "relevance")
    trust = _rating(data, "trust")
    contact_likelihood = _rating(data, "contact_likelihood")
    unmapped: list[str] = []
    signals = _subset(data, "trust_signals_noticed", TRUST_SIGNALS, unmapped)
    missing = _subset(data, "missing_info", MISSING_INFO, unmapped)
    next_step = _canon(data.get("next_step"), NEXT_STEPS)
    assert next_step, f"next_step must be one of {sorted(NEXT_STEPS)}, got {data.get('next_step')!r}"
    basis = _canon(data.get("basis_primary"), BASIS_PRIMARY) or "other"
    strongest = _string(data, "strongest_element")
    weakest = _string(data, "weakest_element")
    improvement = _string(data, "improvement_suggestion")
    tone = _string(data, "tone_and_visuals")
    reason = _string(data, "reason")

    contexts = [
        {
            "key": "decision.primary",
            "label": "Next step after reading the page",
            "contextType": "decision",
            "facets": [
                _facet("decision_outcome", "Decision outcome", "primary", "categorical", next_step),
                _facet("basis_primary", "Primary basis", "primary", "categorical", basis),
                _facet("reason", "Reason", "explanation", "textual", reason, explains="decision_outcome"),
                _facet("decision_subject_label", "Page", "evidence", "categorical", page_label),
                _facet("decision_subject_id", "Page id", "evidence", "categorical", page_id),
                _facet("contact_likelihood", "Likelihood of contacting (1-7)", "score", "numerical",
                       contact_likelihood),
                _facet("converted", "Would engage sales", "primary", "categorical",
                       "true" if next_step in CONVERTING else "false"),
            ],
        },
        {
            "key": f"page_audit.{page_id}",
            "label": f"Page audit: {page_label}",
            "contextType": "page_audit",
            "facets": [
                _facet("page_id", "Page", "primary", "categorical", page_id),
                _facet("clarity", "Clarity", "score", "numerical", clarity),
                _facet("relevance", "Relevance to role", "score", "numerical", relevance),
                _facet("trust", "Trust", "score", "numerical", trust),
                _facet("one_sentence_summary", "Summary", "evidence", "textual", summary),
                _facet("key_claim_noticed", "Key claim noticed", "evidence", "textual", key_claim),
                _facet("trust_signals_noticed", "Trust signals", "evidence", "categorical",
                       ", ".join(signals) or "none"),
                _facet("missing_info", "Missing info", "evidence", "categorical",
                       ", ".join(missing) or "nothing"),
                _facet("tone_and_visuals", "Tone and visuals", "explanation", "textual", tone),
                _facet("tier_page_correct", "Opened own tier page", "evidence", "categorical",
                       tier_page_correct),
                _facet("unmapped_values", "Values needing canonicalisation", "evidence", "categorical",
                       ", ".join(unmapped) or "none"),
                _facet("json_health", "Artifact JSON health", "evidence", "categorical", json_health),
            ],
        },
        {
            # What to change, in the persona's own words — the partner-facing payload.
            "key": f"page_improvement.{page_id}",
            "label": f"How to improve: {page_label}",
            "contextType": "page_improvement",
            "facets": [
                _facet("improvement_suggestion", "Suggested change", "explanation", "textual", improvement),
                _facet("strongest_element", "Strongest element", "evidence", "textual", strongest),
                _facet("weakest_element", "Weakest element", "evidence", "textual", weakest),
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
                       f"The persona audited {page_label} and saved a valid {OUTPUT.name}."),
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
