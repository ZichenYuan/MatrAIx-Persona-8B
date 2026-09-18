#!/bin/bash
# Oracle: a two-page visit (homepage -> pricing) fetched with Playwright, then a
# valid free_visit.json with reference answers. No model; exercises the verifier
# and the reporting pipeline only.
set -euo pipefail
mkdir -p /app/output

python <<'PY'
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

start = "https://infobric.com/se/"
pricing = "https://infobric.com/se/pris-och-paketering/"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto(start, wait_until="domcontentloaded", timeout=60_000)
    page.goto(pricing, wait_until="domcontentloaded", timeout=60_000)
    title = page.title()
    b.close()

Path("/app/output/free_visit.json").write_text(json.dumps({
    "start_url": start,
    "pages_visited": [start, pricing],
    "exit_page": pricing,
    "reached_pricing": True,
    "reached_contact": False,
    "steps_used": 3,
    "stopped_because": "found_enough",
    "found_what_needed": "partly",
    "biggest_obstacle": "Oracle reference answer; not a persona judgment.",
    "conclusion": f"Reference answer after reaching {title}.",
    "clarity": 5, "trust": 5, "contact_likelihood": 3,
    "trust_action": "need_references_first",
    "missing_info": ["references"],
    "next_step": "learn_more",
    "basis_primary": "fit",
    "improvement_suggestion": "Oracle reference answer; not a persona judgment.",
    "reason": "Oracle reference answer; not a persona judgment.",
}, indent=2, ensure_ascii=False) + "\n")
PY
