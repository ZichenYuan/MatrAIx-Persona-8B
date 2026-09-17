"""Verifier — Infobric page-audit task.

Validity gate: the persona must have saved a well-formed page_audit.json.
Everything it wrote is surfaced as structured facets so `matraix results
--group-by <dimension>` and reporting.json can aggregate it.

Facet contract follows application/task-spec/web/README.md § "Required Facets
For `decision`": decision_outcome, basis_primary, reason, decision_subject_label,
decision_subject_id. Audit-specific ratings live in their own `page_audit`
context so the generic contract and task data stay separate.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

OUTPUT = Path("/app/output/page_audit.json")
PAGE_URL = "https://infobric.com/se/"

TRUST_SIGNALS = {"logos", "customer_count", "testimonial", "case_studies", "certifications"}
MISSING_INFO = {
    "price", "integrations", "hardware", "setup_time", "references", "data_privacy", "contract_terms",
}
NEXT_STEPS = {"contact_sales", "book_demo", "try_free", "learn_more", "come_back_later", "leave"}
BASIS_PRIMARY = {
    "price", "quality", "features", "convenience", "taste", "trust", "familiarity", "novelty", "fit", "other",
}
# next_step buckets that count as a converted lead — the study's headline metric.
CONVERTING = {"contact_sales", "book_demo", "try_free"}


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


def _string(data: dict, key: str) -> str:
    value = data.get(key)
    assert isinstance(value, str) and value.strip(), f"{key} must be a non-empty string"
    return value.strip()


# Models reliably produce near-misses for these enums ("customer_logos" for
# "logos", "testimonials" for "testimonial"). The value is unambiguous, so map it
# rather than throwing away a whole trial. Anything still unrecognised is dropped
# and reported in an `unmapped_values` facet so the rate stays visible.
_ALIASES = {
    "customer_logos": "logos", "client_logos": "logos", "brand_logos": "logos",
    "customer_testimonial": "testimonial", "testimonials": "testimonial",
    "customer_testimonials": "testimonial", "quotes": "testimonial",
    "customer_stories": "case_studies", "case_study": "case_studies",
    "customer_cases": "case_studies", "references": "case_studies",
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


def _canon(raw: object, allowed: set[str]) -> str | None:
    """Map a model-written token onto the allowed enum, or None."""
    token = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    for candidate in (
        token,
        _ALIASES.get(token),
        token[:-1] if token.endswith("s") else None,          # plural
        token.split("_", 1)[-1] if "_" in token else None,     # "customer_logos" → "logos"
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


def test_output_schema() -> None:
    data = json.loads(OUTPUT.read_text())
    assert isinstance(data, dict), "root must be an object"

    assert data.get("page_url") == PAGE_URL, f"page_url must be {PAGE_URL}"
    page_id = _string(data, "page_id")
    page_label = _string(data, "page_label")
    summary = _string(data, "one_sentence_summary")
    fact = _string(data, "fact_customers_claimed")
    clarity = _rating(data, "clarity")
    relevance = _rating(data, "relevance")
    trust = _rating(data, "trust")
    unmapped: list[str] = []
    signals = _subset(data, "trust_signals_noticed", TRUST_SIGNALS, unmapped)
    missing = _subset(data, "missing_info", MISSING_INFO, unmapped)
    # The two decision fields stay strict-after-canonicalisation: an unreadable
    # next_step makes the record meaningless, so that one still fails the trial.
    next_step = _canon(data.get("next_step"), NEXT_STEPS)
    assert next_step, f"next_step must be one of {sorted(NEXT_STEPS)}, got {data.get('next_step')!r}"
    basis = _canon(data.get("basis_primary"), BASIS_PRIMARY) or "other"
    tone = _string(data, "tone_and_visuals")
    reason = _string(data, "reason")

    contexts = [
        {
            # Standard shape the reporting lens reads (task-spec/web/README.md).
            "key": "decision.primary",
            "label": "Next step after reading the page",
            "contextType": "decision",
            "facets": [
                _facet("decision_outcome", "Decision outcome", "primary", "categorical", next_step),
                _facet("basis_primary", "Primary basis", "primary", "categorical", basis),
                _facet("reason", "Reason", "explanation", "textual", reason, explains="decision_outcome"),
                _facet("decision_subject_label", "Page", "evidence", "categorical", page_label),
                _facet("decision_subject_id", "Page id", "evidence", "categorical", page_id),
                _facet("converted", "Would engage sales", "primary", "categorical",
                       "true" if next_step in CONVERTING else "false"),
            ],
        },
        {
            # Audit-specific ratings and observations.
            "key": f"page_audit.{page_id}",
            "label": f"Page audit: {page_label}",
            "contextType": "page_audit",
            "facets": [
                _facet("clarity", "Clarity", "score", "numerical", clarity),
                _facet("relevance", "Relevance to role", "score", "numerical", relevance),
                _facet("trust", "Trust", "score", "numerical", trust),
                _facet("one_sentence_summary", "Summary", "evidence", "textual", summary),
                _facet("fact_customers_claimed", "Customers claimed", "evidence", "categorical", fact),
                _facet("trust_signals_noticed", "Trust signals", "evidence", "categorical",
                       ", ".join(signals) or "none"),
                _facet("missing_info", "Missing info", "evidence", "categorical",
                       ", ".join(missing) or "nothing"),
                _facet("tone_and_visuals", "Tone and visuals", "explanation", "textual", tone),
                _facet("unmapped_values", "Values needing canonicalisation", "evidence", "categorical",
                       ", ".join(unmapped) or "none"),
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
