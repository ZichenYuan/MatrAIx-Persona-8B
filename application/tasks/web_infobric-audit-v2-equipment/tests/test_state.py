"""Verifier — Infobric page audit v2.

Validity gate plus two output files for one page of infobric.com, reviewed as a
standalone entry point with a single click on the page's primary next-step button.
Design: docs/superpowers/specs/2026-09-18-infobric-audit-v2-design.md.

Two files, two audiences:

- ``structured_output.json`` — what the partner report renders. Only facets that map to
  a section of the partner's brief: the six dimensions (1-5), whether the first screen
  kept them reading, how well the button matched its expectation, the next step and
  what they would need before going further, and four composite texts the report's
  summaries are written from. Chartable facets are kept to a dozen on purpose: the
  report crosses every chartable facet with every persona dimension it is allowed to.
- ``quality.json`` — everything about whether the simulation behaved: grounding of
  quoted wording against the page inventory, CTA label and destination checks,
  persona fidelity (self-briefing vs profile), instrument version, variant, JSON
  health, and a copy of every raw score. Read by the ablation tooling, never by the
  report.

Deterministic on purpose: no model calls. Inputs besides the artifact:
``/app/input/inventory.json`` (hand-checked page ground truth) and
``/app/input/persona.yaml`` (uploaded by the persona agent). Paths come from the
environment so the same code runs on the host in unit tests.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

INSTRUMENT_VERSION = "2.4"

OUTPUT = Path(os.environ.get("AUDIT_OUTPUT", "/app/output/page_audit.json"))
INPUT_DIR = Path(os.environ.get("AUDIT_INPUT_DIR", "/app/input"))
INVENTORY = INPUT_DIR / "inventory.json"
PERSONA = INPUT_DIR / "persona.yaml"
VARIANT_FILE = INPUT_DIR / "variant.txt"

POSITIONS = {"top", "middle", "bottom"}
KINDS = {"confusing", "missing", "unconvincing", "irrelevant"}
ARRIVED = {"specific_problem", "exploring", "existing_customer", "other_reason"}
YES_NO = {"yes", "no"}
# Trust as a ladder of commitments (instrument 2.4): four rungs of rising cost, plus one
# belief item. trust_ladder = rungs answered yes (0-4); consistency = no yes above a no.
TRUST_LADDER = ("trust_email_guide", "trust_callback", "trust_demo_week", "trust_pilot_data")
TRUST_CLAIM = "trust_claim_unchecked"
TRUST_ACTS = TRUST_LADDER + (TRUST_CLAIM,)
ALL_NEXT_STEPS = {
    "book_demo", "start_trial", "create_free_account", "order_package", "use_calculator",
    "download_guide", "preview_fleet", "contact_sales", "learn_more", "come_back_later", "leave",
    "go_to_login", "go_elsewhere_on_site",
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
    "end": "bottom", "unclear": "confusing", "absent": "missing", "not_convincing": "unconvincing",
    "pricing": "price", "prices": "price", "cost": "price", "integration": "integrations",
    "setup": "setup_time", "privacy": "data_privacy", "gdpr": "data_privacy",
    "contract": "contract_terms", "terms": "contract_terms", "customer_references": "references",
    "demo": "book_demo", "trial": "start_trial", "free_trial": "start_trial",
    "free_account": "create_free_account", "calculator": "use_calculator", "guide": "download_guide",
    "contact": "contact_sales", "contact_us": "contact_sales",
    "references_first": "need_references_first", "pilot_first": "need_pilot_first",
    "share_now": "share_data_now", "would_not": "would_not_proceed",
    "customer": "existing_customer", "existing": "existing_customer", "other": "other_reason",
    "login": "go_to_login", "log_in": "go_to_login", "support": "go_to_login",
    "careers": "go_elsewhere_on_site", "career_page": "go_elsewhere_on_site", "contact_page": "go_elsewhere_on_site",
    "elsewhere": "go_elsewhere_on_site", "other_page": "go_elsewhere_on_site", "navigate": "go_elsewhere_on_site",
}
# Last-resort keyword mapping, checked in order, only within the allowed set.
_KEYWORDS = (
    ("customer", "existing_customer"), ("log in", "go_to_login"), ("login", "go_to_login"),
    ("job", "other_reason"), ("sell", "other_reason"), ("assignment", "other_reason"),
    ("mistake", "other_reason"), ("research", "other_reason"),
    ("specific", "specific_problem"), ("problem", "specific_problem"), ("explor", "exploring"),
    ("would not", "would_not_proceed"), ("reference", "need_references_first"),
    ("pilot", "need_pilot_first"), ("trial", "need_pilot_first"), ("share", "share_data_now"),
)


# --------------------------------------------------------------------------- helpers
def _verifier_dir() -> Path:
    explicit = os.environ.get("HARBOR_VERIFIER_DIR")
    path = Path(explicit) if explicit else Path("/logs/verifier")
    path.mkdir(parents=True, exist_ok=True)
    return path


# What a *real* closing quote is followed by. In an object, a comma only ends the
# string when a new "key": follows; in an array, a comma followed by the next element
# does. Anything else (", which overlaps", " in ", ", the phone") is prose.
_STRING_END_IN_OBJECT = re.compile(r'\s*(?:,\s*"[A-Za-z_][A-Za-z0-9_]*"\s*:|[}\]:]|$)', re.M)
_STRING_END_IN_ARRAY = re.compile(r'\s*(?:,\s*(?:["{\[]|$)|[}\]]|$)', re.M)


def _escape_inner_quotes(raw: str) -> str:
    """Escape double quotes that models leave unescaped inside string values when
    they quote page wording ("retain": "Keep "Vi digitaliserar byggbranschen" ...")."""
    out: list[str] = []
    stack: list[str] = []
    in_string = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if not in_string:
            if ch == '"':
                in_string = True
            elif ch in "{[":
                stack.append(ch)
            elif ch in "}]" and stack:
                stack.pop()
            out.append(ch)
        elif ch == "\\":
            out.append(raw[i : i + 2])
            i += 1
        elif ch == '"':
            end = _STRING_END_IN_ARRAY if stack and stack[-1] == "[" else _STRING_END_IN_OBJECT
            if end.match(raw, i + 1):
                in_string = False
                out.append(ch)
            else:
                out.append('\\"')
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _clean_json_syntax(text: str) -> str:
    """Two more slips seen in the wild: a trailing comma before a closing bracket
    or brace, and a stray character between a closing quote and the next delimiter
    (`"...text">,`). Neither can occur in valid JSON, so removing them is safe; the
    result is always re-parsed before it is trusted."""
    text = re.sub(r",(\s*[\]}])", r"\1", text)
    text = re.sub(r'"[ \t]*[^\w\s,\]}:"]{1,3}\s*(?=[,\]}])', '"', text)
    return text

def _load_json_lenient(path: Path) -> tuple[dict, str]:
    """Parse the artifact, repairing the three defects models actually produce and
    recording which: raw control characters inside strings, unescaped quotes inside
    strings (quoted page wording), and a final string whose closing quote was cut off
    by the file tool (the file ends `...text\n}`)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(raw), "clean"
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(raw, strict=False), "repaired_control_chars"
    except json.JSONDecodeError as exc:
        first_error = exc
    # Try the repairs in every useful order; the first text that parses wins.
    candidates = [
        ("repaired_inner_quotes", _escape_inner_quotes(raw)),
        ("repaired_syntax", _clean_json_syntax(raw)),
        ("repaired_inner_quotes", _escape_inner_quotes(_clean_json_syntax(raw))),
        ("repaired_inner_quotes", _clean_json_syntax(_escape_inner_quotes(raw))),
    ]
    tried = {raw}
    for label, text in candidates:
        if text in tried:
            continue
        tried.add(text)
        try:
            return json.loads(text, strict=False), label
        except json.JSONDecodeError:
            pass
    # A complete object followed by leftovers (an extra `}` or stray text after the
    # closing brace): take the first complete value and ignore the rest.
    for text in [raw, *(t for _, t in candidates)]:
        try:
            value, end = json.JSONDecoder(strict=False).raw_decode(text.lstrip())
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and not text.lstrip()[end:].strip(" \t\r\n}]"):
            return value, "repaired_trailing_data"
    if "Unterminated string" not in str(first_error):
        raise first_error
    # Close the unterminated string at the end of its line, then close the object.
    lines = raw.rstrip().split("\n")
    while lines and lines[-1].strip() in {"}", ""}:
        lines.pop()
    if lines:
        lines[-1] = lines[-1].rstrip().rstrip(",") + '"'
    repaired = "\n".join(lines) + "\n}\n"
    return json.loads(repaired, strict=False), "repaired_unterminated_string"


def _inventory() -> dict:
    return json.loads(INVENTORY.read_text(encoding="utf-8")) if INVENTORY.is_file() else {}


def _persona_field(key: str) -> str | None:
    if not PERSONA.is_file():
        return None
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", PERSONA.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip().strip("'\"") if match else None


def _canon(raw: object, allowed: set[str]) -> str | None:
    """Map a model-written value onto an enum. Models often append an explanation
    ("specific_problem — I need…"), so the value is also tried as the text before the
    first separator, and finally by keyword."""
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


def _string_or_unknown(data: dict, key: str, max_len: int = 3000) -> str:
    """Like _string, but an absent, empty or 'unknown' value is allowed (early exit)."""
    value = data.get(key)
    if value is None or (isinstance(value, str) and (not value.strip() or value.strip().lower() == "unknown")):
        return "unknown"
    assert isinstance(value, str), f"{key} must be a string"
    return value.strip()[:max_len]


def _bool_or_false(data: dict, key: str) -> bool:
    value = data.get(key)
    if value is None or (isinstance(value, str) and value.strip().lower() in {"", "unknown"}):
        return False
    return _bool(data, key)


def _string(data: dict, key: str, max_len: int = 3000) -> str:
    value = data.get(key)
    assert isinstance(value, str) and value.strip(), f"{key} must be a non-empty string"
    return value.strip()[:max_len]


def _score(data: dict, key: str, allow_unknown: bool = False) -> int | str:
    """A 1-5 rating. Numeric strings ("4") are accepted - models write them often -
    and recorded as numbers; anything else fails unless `unknown` is allowed."""
    value = data.get(key)
    if allow_unknown and (value is None or str(value).strip().lower() == "unknown"):
        return "unknown"
    if isinstance(value, str) and re.fullmatch(r"\s*[1-5](\.0)?\s*", value):
        value = int(float(value))
    assert isinstance(value, (int, float)) and not isinstance(value, bool), f"{key} must be a number 1-5"
    assert 1 <= value <= 5, f"{key} must be 1-5, got {value}"
    return int(value)


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
    return len(hits), len(quotes), [q[:80] for q in quotes if q not in hits]


def _facet(key: str, label: str, role: str, kind: str, value, explains: str | None = None) -> dict:
    out = {"key": key, "label": label, "role": role, "kind": kind, "value": value}
    if explains:
        out["explainsFacetKey"] = explains
    return out


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


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
    cta_labels = [_norm(c) for c in [str(inv.get("primary_cta", {}).get("label") or "")]
                  + [str(c.get("label") or "") for c in inv.get("secondary_ctas") or []] if c]
    cta_fragments = [f for f in [str(inv.get("primary_cta", {}).get("url_fragment") or "")]
                     + [str(c.get("url_fragment") or "") for c in inv.get("secondary_ctas") or []] if f]
    unmapped: list[str] = []
    variant = VARIANT_FILE.read_text(encoding="utf-8").strip() if VARIANT_FILE.is_file() else "full"

    # --- A. self-briefing (fidelity; never fails the trial) ---------------------
    self_briefing = _string(data, "self_briefing")
    intent = (_persona_field("visit_intent") or "").lower()
    persona_arrived = (
        "existing_customer" if "existing customer" in intent
        else "other_reason" if any(w in intent for w in ("job opening", "sell ", "assignment", "by mistake"))
        else "specific_problem" if "specific problem" in intent
        else "exploring" if "exploring" in intent else None
    )
    arrived = _canon(data.get("arrived_with"), ARRIVED)
    if arrived is None:
        unmapped.append(f"arrived_with:{str(data.get('arrived_with'))[:60]}")
        arrived = persona_arrived or "exploring"
    arrived_matches = "n/a" if persona_arrived is None else ("true" if persona_arrived == arrived else "false")

    # --- B. first screen ------------------------------------------------------
    first_takeaway = _string(data, "first_screen_takeaway")
    would_continue = _canon(data.get("would_continue"), YES_NO)
    assert would_continue, "would_continue must be yes or no"
    would_continue_reason = _string(data, "would_continue_reason")
    left_early = _bool_or_false(data, "left_early")
    early = left_early
    if left_early and would_continue != "no":
        unmapped.append("left_early:true with would_continue:yes")
    if not left_early and would_continue == "no":
        unmapped.append("would_continue:no but kept reading")

    # --- C. full page ---------------------------------------------------------
    what_it_does = _string_or_unknown(data, "what_it_does") if early else _string(data, "what_it_does")
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
        confusing.append({
            "what": str(item["what"]).strip()[:300],
            "where": _canon(item.get("where"), POSITIONS) or "unknown",
            "kind": _canon(item.get("kind"), KINDS) or "confusing",
        })
    strongest = _string_or_unknown(data, "strongest_element") if early else _string(data, "strongest_element")
    strongest_pos = _canon(data.get("strongest_position"), POSITIONS) or "unknown"
    weakest = _string_or_unknown(data, "weakest_element") if early else _string(data, "weakest_element")
    weakest_pos = _canon(data.get("weakest_position"), POSITIONS) or "unknown"
    hesitate = _string_or_unknown(data, "hesitate_or_leave_reason") if early else _string(data, "hesitate_or_leave_reason")
    ladder_reason = _string_or_unknown(data, "trust_ladder_reason")
    scores = {"understanding": _score(data, "understanding", allow_unknown=early)}
    for k in SCORES[1:]:
        scores[k] = _score(data, k, allow_unknown=early)
    # Trust as three concrete acts (ablation arm 6). Required on every visit, incl.
    # early exits, but a missing answer is recorded as unmapped rather than failing
    # the trial - the summary reports how often that happens.
    trust_acts_answers: dict[str, str] = {}
    for k in TRUST_ACTS:
        answer = _canon(data.get(k), YES_NO)
        if answer is None:
            unmapped.append(f"{k}:{str(data.get(k))[:40]}")
            answer = "unknown"
        trust_acts_answers[k] = answer
    rungs = [trust_acts_answers[k] for k in TRUST_LADDER]
    trust_ladder: int | str = sum(1 for v in rungs if v == "yes") if all(v != "unknown" for v in rungs) else "unknown"
    # Guttman check: once a rung is refused, every higher rung should be refused too.
    if trust_ladder == "unknown":
        trust_ladder_consistent = "unknown"
    else:
        first_no = next((i for i, v in enumerate(rungs) if v == "no"), len(rungs))
        trust_ladder_consistent = "yes" if all(v == "no" for v in rungs[first_no:]) else "no"

    # --- D. CTA hop -----------------------------------------------------------
    cta_seen = _string_or_unknown(data, "primary_cta_seen") if early else _string(data, "primary_cta_seen")
    cta_expectation = _string_or_unknown(data, "cta_expectation") if early else _string(data, "cta_expectation")
    cta_inspected = _bool_or_false(data, "cta_inspected") if early else _bool(data, "cta_inspected")
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
    improvement_check = _string_or_unknown(data, "improvement_check") if early else _string(data, "improvement_check")
    retain = _string_or_unknown(data, "retain") if early else _string(data, "retain")

    # --- grounding against the page snapshot ----------------------------------
    c_hit, c_tot, c_miss = _grounding(credible + need_proof, snapshot)
    p_hit, p_tot, p_miss = _grounding(familiar + off, snapshot)

    # --- composite texts: the report's four summaries are written from these ----
    takeaway_text = (
        f"First screen: {first_takeaway}\n"
        f"Would keep reading after the first screen: {would_continue} — {would_continue_reason}\n"
        + ("Left after the first screen; the rest of the page was not read.\n" if early else "")
        +         f"After reading everything: {what_it_does}\n"
        f"Own problems recognised:\n{_bullets(problems)}\n"
        f"Next step: {next_step}. Would need before going further: {trust_action}. Why: {reason}"
    )
    findings_text = (
        "Confusing, missing, unconvincing or irrelevant [position/kind]:\n"
        + _bullets([f"[{c['where']}/{c['kind']}] {c['what']}" for c in confusing])
        + "\nClaims that need proof (quoted):\n" + _bullets(need_proof)
        + "\nClaims found credible (quoted):\n" + _bullets(credible)
        + "\nWording that felt written for someone else (quoted):\n" + _bullets(off)
        + "\nWording that felt familiar (quoted):\n" + _bullets(familiar)
        + f"\nMissing information: {', '.join(missing) or 'nothing named'}"
        + f"\nWeakest element [{weakest_pos}]: {weakest}"
        + f"\nWhat would cause hesitation or leaving: {hesitate}"
        + f"\nWhy they stop where they stop on the commitment ladder: {ladder_reason}"
    )
    cta_text = (
        f"Button seen: «{cta_seen}». Expected before clicking: {cta_expectation}\n"
        + (f"Clicked and inspected: yes. Reached: {cta_url}\nWhat followed: {cta_reality}\n"
           f"The form asks for: {', '.join(form_asks) or 'no form seen'}"
           if cta_inspected else "Clicked and inspected: no — not assessed (unknown).")
    )
    changes_text = (
        f"Change: {improvement}\nHow to check whether it helped: {improvement_check}\n"
        f"Keep: {retain}\nStrongest element [{strongest_pos}]: {strongest}"
    )

    contexts = [
        {
            "key": "decision.primary",
            "label": "Next step after the page",
            "contextType": "decision",
            "facets": [
                _facet("decision_outcome", "Next step", "primary", "categorical", next_step),
                _facet("basis_primary", "Primary basis", "primary", "categorical", basis),
                _facet("reason", "Reason", "explanation", "textual", reason, explains="decision_outcome"),
                _facet("decision_subject_label", "Page", "evidence", "categorical", page_label),
                _facet("decision_subject_id", "Page id", "evidence", "categorical", page_id),
                _facet("trust_action", "Needed before going further", "primary", "categorical", trust_action),
                _facet("contact_likelihood", "Likelihood of contacting (1-5)", "score", "numerical", contact),
            ],
        },
        {
            "key": "first_impression.primary",
            "label": "First screen, before scrolling",
            "contextType": "first_impression",
            "facets": [
                _facet("would_continue", "Would keep reading after the first screen", "primary", "categorical",
                       would_continue),
                _facet("left_early", "Left after the first screen", "primary", "categorical",
                       "true" if early else "false"),
                _facet("would_continue_reason", "Why", "explanation", "textual", would_continue_reason,
                       explains="would_continue"),
            ],
        },
        {
            "key": f"page_audit.{page_id}",
            "label": f"Page audit: {page_label}",
            "contextType": "page_audit",
            "facets": [
                _facet("understanding", "Understanding (1-5)", "score",
                       "numerical" if scores["understanding"] != "unknown" else "categorical", scores["understanding"]),
                _facet("language_relevance", "Language and relevance (1-5)", "score",
                       "numerical" if scores["language_relevance"] != "unknown" else "categorical", scores["language_relevance"]),
                _facet("practical_value", "Perceived practical value (1-5)", "score",
                       "numerical" if scores["practical_value"] != "unknown" else "categorical", scores["practical_value"]),
                _facet("trust", "Trust (1-5)", "score",
                       "numerical" if scores["trust"] != "unknown" else "categorical", scores["trust"]),
                _facet("trust_ladder", "Trust ladder: rungs accepted this week (0-4)", "score",
                       "numerical" if trust_ladder != "unknown" else "categorical", trust_ladder),
                _facet("trust_ladder_consistent", "Trust ladder answered consistently (no yes above a no)", "score",
                       "categorical", trust_ladder_consistent),
                _facet("trust_email_guide", "Would give a work email for a guide", "score", "categorical",
                       trust_acts_answers["trust_email_guide"]),
                _facet("trust_callback", "Would ask for a call-back", "score", "categorical",
                       trust_acts_answers["trust_callback"]),
                _facet("trust_demo_week", "Would book a demo this week", "score", "categorical",
                       trust_acts_answers["trust_demo_week"]),
                _facet("trust_pilot_data", "Would run a pilot on own data this month", "score", "categorical",
                       trust_acts_answers["trust_pilot_data"]),
                _facet("trust_claim_unchecked", "Would accept the proof claim unchecked", "score", "categorical",
                       trust_acts_answers["trust_claim_unchecked"]),
                _facet("next_step_confidence", "Confidence in the next step (1-5)", "score",
                       "numerical" if scores["next_step_confidence"] != "unknown" else "categorical", scores["next_step_confidence"]),
                _facet("next_step_ease", "Ease of completing the next step (1-5)", "score",
                       "numerical" if ease != "unknown" else "categorical", ease),
                _facet("takeaway_text", "What they understood and would do next", "explanation", "textual",
                       takeaway_text),
                _facet("findings_text", "Findings, with exact wording", "explanation", "textual", findings_text),
            ],
        },
        {
            "key": "cta_followthrough.primary",
            "label": "The primary next-step button",
            "contextType": "cta_followthrough",
            "facets": [
                _facet("cta_match", "What followed matched expectation (1-5)", "score",
                       "numerical" if cta_match != "unknown" else "categorical", cta_match),
                _facet("cta_text", "Expectation vs what followed", "explanation", "textual", cta_text),
            ],
        },
        {
            "key": f"page_improvement.{page_id}",
            "label": f"How to improve: {page_label}",
            "contextType": "page_improvement",
            "facets": [
                _facet("changes_text", "What to change, how to check, what to keep", "explanation", "textual",
                       changes_text),
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

    out_dir = _verifier_dir()
    (out_dir / "structured_output.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "artifactType": "matraix.trial_evaluation",
                "taskType": "web",
                "presenceCheck": {"passed": True, "requiredArtifacts": [OUTPUT.name], "missingArtifacts": []},
                "sourceArtifacts": {"taskOutput": str(OUTPUT)},
                "contexts": contexts,
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    # Quality / ablation layer. Never rendered by the partner report.
    (out_dir / "quality.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "artifactType": "matraix.audit_quality",
                "instrument_version": INSTRUMENT_VERSION,
                "variant": variant,
                "device_reviewed": "desktop",
                "page_id": page_id,
                "json_health": json_health,
                "unmapped_values": unmapped,
                "persona": {
                    "display_name": _persona_field("display_name"),
                    "audience_group": _persona_field("audience_group"),
                    "tier": _persona_field("tier"),
                    "visit_intent": _persona_field("visit_intent"),
                    "infobric_familiarity": _persona_field("infobric_familiarity"),
                    "traffic_segment": _persona_field("traffic_segment"),
                },
                "exit": {"left_early": early, "would_continue": would_continue},
                "fidelity": {
                    "self_briefing": self_briefing,
                    "arrived_with": arrived,
                    "persona_arrived_with": persona_arrived,
                    "arrived_with_matches_persona": arrived_matches,
                },
                "grounding": {
                    "claims_quoted": c_tot, "claims_grounded": c_hit,
                    "claims_grounded_share": round(c_hit / c_tot, 3) if c_tot else None,
                    "phrases_quoted": p_tot, "phrases_grounded": p_hit,
                    "phrases_grounded_share": round(p_hit / p_tot, 3) if p_tot else None,
                    "ungrounded_quotes": c_miss + p_miss,
                },
                "cta": {
                    "primary_cta_seen": cta_seen, "cta_label_grounded": cta_label_grounded,
                    "cta_inspected": cta_inspected, "cta_page_url": cta_url, "cta_url_ok": cta_url_ok,
                },
                "scores_in_browse": {**scores, "next_step_ease": ease, "cta_match": cta_match,
                                     "contact_likelihood": contact, "trust_ladder": trust_ladder,
                                     "trust_ladder_consistent": trust_ladder_consistent, **trust_acts_answers},
                "decision": {"next_step": next_step, "converted": next_step in conversions,
                             "basis_primary": basis, "trust_action": trust_action},
                "trust_ladder_reason": ladder_reason,
                "counts": {"confusing_or_missing": len(confusing), "problems_recognised": len(problems),
                           "claims_need_proof": len(need_proof), "claims_credible": len(credible),
                           "language_felt_off": len(off), "language_felt_familiar": len(familiar),
                           "form_asks_for": len(form_asks)},
                "missing_info": missing,
                "positions": {"strongest": strongest_pos, "weakest": weakest_pos,
                              "confusing_or_missing": [c["where"] for c in confusing]},
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
