#!/bin/bash
# Oracle: fetch the briefed page with Playwright and write a valid audit, no model.
# The page comes from the job's extra_instruction_paths brief, which the oracle
# cannot read, so it defaults to the homepage — enough to exercise the verifier.
set -euo pipefail
mkdir -p /app/output

python <<'PY'
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright

page_id = os.environ.get("AUDIT_PAGE_ID", "homepage")
urls = {
    "homepage": "https://infobric.com/se/",
    "pricing": "https://infobric.com/se/pris-och-paketering/",
    "tier_page": "https://infobric.com/se/vem-vi-hjalper/huvudentreprenorer/",
}
url = urls[page_id]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    title = page.title()
    b.close()

Path("/app/output/page_audit.json").write_text(json.dumps({
    "page_id": page_id,
    "page_url": url,
    "one_sentence_summary": f"Reference answer for {title}.",
    "key_claim_noticed": "none",
    "clarity": 5, "relevance": 4, "trust": 5, "contact_likelihood": 3,
    "trust_signals_noticed": ["logos"],
    "missing_info": ["price"],
    "next_step": "learn_more",
    "basis_primary": "fit",
    "strongest_element": "the headline",
    "weakest_element": "the absence of pricing",
    "improvement_suggestion": "Oracle reference answer; not a persona judgment.",
    "tone_and_visuals": "Corporate, calm, photo-led.",
    "reason": "Oracle reference answer; not a persona judgment.",
}, indent=2, ensure_ascii=False) + "\n")
PY
