#!/bin/bash
# Oracle: open the page from input/inventory.json, click its primary CTA once with
# Playwright, and write a valid page_audit.json with reference answers. No model;
# exercises the verifier, the grounding checks and the reporting pipeline only.
set -euo pipefail
mkdir -p /app/output

python <<'PY'
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

inv = json.loads(Path("/app/input/inventory.json").read_text(encoding="utf-8"))
url = inv["url"]
cta = inv.get("primary_cta") or {}
label = cta.get("label") or ""
claims = inv.get("claims") or []
steps = inv.get("available_next_steps") or ["learn_more"]

cta_url, cta_inspected = "unknown", False
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    title = page.title()
    if label:
        try:
            page.get_by_role("link", name=label, exact=True).first.click(timeout=10_000)
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            cta_url, cta_inspected = page.url, True
        except Exception as exc:  # noqa: BLE001 - fall back to the known target
            print(f"[oracle] CTA click failed ({exc}); opening the CTA target directly")
            frag = cta.get("url_fragment") or ""
            if frag and not frag.startswith("#"):
                base = url.split("/se/")[0] + "/se"
                page.goto(base + frag + ("/" if not frag.endswith("/") else ""), wait_until="domcontentloaded", timeout=60_000)
                cta_url, cta_inspected = page.url, True
    b.close()

quote = claims[0] if claims else "none"
Path("/app/output/page_audit.json").write_text(json.dumps({
    "self_briefing": "Oracle reference answer; not a persona judgment.",
    "arrived_with": "exploring",
    "first_screen_takeaway": f"Reference answer for {title}.",
    "first_screen_expectation_match": 3,
    "would_continue": "yes",
    "would_continue_reason": "Oracle reference answer.",
    "what_it_does": inv.get("truth_statement") or "Oracle reference answer.",
    "problems_recognised": [],
    "language_felt_familiar": [],
    "language_felt_off": [],
    "claims_credible": [quote] if claims else [],
    "claims_need_proof": [],
    "confusing_or_missing": [{"what": "Oracle placeholder", "where": "middle", "kind": "missing"}],
    "dead_click_candidates": [],
    "attention_stop_point": "middle",
    "strongest_element": "the headline",
    "strongest_position": "top",
    "weakest_element": "the absence of pricing",
    "weakest_position": "bottom",
    "hesitate_or_leave_reason": "Oracle reference answer.",
    "understanding": 3, "language_relevance": 3, "practical_value": 3, "trust": 3,
    "next_step_confidence": 3,
    "next_step_ease": 3 if cta_inspected else "unknown",
    "primary_cta_seen": label or "unknown",
    "cta_expectation": "A contact form.",
    "cta_inspected": cta_inspected,
    "cta_page_url": cta_url,
    "cta_reality": "Oracle reference answer." if cta_inspected else "unknown",
    "form_asks_for": [],
    "cta_match": 3 if cta_inspected else "unknown",
    "next_step": steps[-1] if "learn_more" not in steps else "learn_more",
    "basis_primary": "fit",
    "trust_action": "need_references_first",
    "contact_likelihood": 2,
    "missing_info": ["price"],
    "reason": "Oracle reference answer; not a persona judgment.",
    "improvement_suggestion": "Oracle reference answer; not a persona judgment.",
    "improvement_check": "Oracle reference answer.",
    "retain": "Oracle reference answer.",
}, indent=2, ensure_ascii=False) + "\n")
PY
