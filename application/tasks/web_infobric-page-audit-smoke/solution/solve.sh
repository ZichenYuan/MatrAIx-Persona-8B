#!/bin/bash
# Oracle: fetch the page with Playwright and write a valid audit without a model.
set -euo pipefail
mkdir -p /app/output

python <<'PY'
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

url = "https://infobric.com/se/"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    text = page.inner_text("body")
    b.close()

m = re.search(r"(\d[\d\s.,]*)\s*(kunder|customers|användare|users)", text, re.I)
fact = m.group(0).strip() if m else "not found"

Path("/app/output/page_audit.json").write_text(json.dumps({
    "page_url": url,
    "page_id": "homepage",
    "page_label": "Infobric homepage",
    "one_sentence_summary": "Infobric offers systems that make construction sites safer and more efficient.",
    "fact_customers_claimed": fact,
    "clarity": 5, "relevance": 4, "trust": 5,
    "trust_signals_noticed": ["logos"],
    "missing_info": ["price"],
    "next_step": "learn_more",
    "basis_primary": "fit",
    "tone_and_visuals": "Corporate, calm, photo-led.",
    "reason": "Oracle reference answer; not a persona judgment.",
}, indent=2, ensure_ascii=False) + "\n")
PY
