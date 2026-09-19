"""reporting.json ``personaDimensions``: a task may restrict which persona dimensions
Persona insights crosses by (default card axes and the explorer picker)."""

from backend.service.job_aggregation import _reporting_persona_dimension_allowlist


def test_allowlist_absent_or_malformed_means_no_restriction():
    assert _reporting_persona_dimension_allowlist(None) == []
    assert _reporting_persona_dimension_allowlist("audience_group") == []
    assert _reporting_persona_dimension_allowlist({"a": 1}) == []
    assert _reporting_persona_dimension_allowlist([]) == []


def test_allowlist_keeps_order_and_dedupes_and_strips():
    raw = [" audience_group", "tier", "audience_group", "", "  ", "visit_intent"]
    assert _reporting_persona_dimension_allowlist(raw) == ["audience_group", "tier", "visit_intent"]


def test_allowlist_coerces_non_strings():
    assert _reporting_persona_dimension_allowlist(["tier", 7]) == ["tier", "7"]
