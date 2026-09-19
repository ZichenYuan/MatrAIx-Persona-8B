#!/usr/bin/env python3
"""Draft a page inventory (ground truth) for the Infobric page-audit v2 task.

Fetches the page, extracts its visible text, headings, call-to-action candidates and
claim candidates, and writes a draft `pages/<page_id>.inventory.json` for a person to
check and complete. The verifier grounds quoted wording against `text_snapshot` and
the CTA labels/targets, so the draft must be confirmed by eye before use.

    uv run python application/scripts/build_inventory.py --page-id homepage \
        --url https://infobric.com/se/ [--out application/task-templates/web_infobric-audit-v2/pages]

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

CTA_WORDS = (
    "kontakt", "demo", "prova", "testa", "skapa konto", "boka", "räkna", "kalkyl",
    "ladda ner", "offert", "beställ", "köp", "kom igång", "starta", "visa min",
    "contact", "trial", "book", "get started",
)
SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "template", "iframe"}


class _Extract(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._href: str | None = None
        self._link_text: list[str] = []
        self._heading: str | None = None
        self._heading_text: list[str] = []
        self.text: list[str] = []
        self.headings: list[tuple[str, str, int]] = []   # (tag, text, char offset)
        self.links: list[tuple[str, str]] = []           # (text, href)
        self._chars = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip += 1
            return
        a = dict(attrs)
        if tag in ("a", "button"):
            self._href = a.get("href") or ""
            self._link_text = []
        if tag in ("h1", "h2", "h3"):
            self._heading = tag
            self._heading_text = []
        if tag in ("p", "li", "div", "section", "br", "h1", "h2", "h3", "h4", "td", "th"):
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if tag in ("a", "button") and self._href is not None:
            t = " ".join(" ".join(self._link_text).split())
            if t:
                self.links.append((t, self._href))
            self._href = None
        if tag == self._heading:
            t = " ".join(" ".join(self._heading_text).split())
            if t:
                self.headings.append((tag, t, self._chars))
            self._heading = None

    def handle_data(self, data):
        if self._skip:
            return
        s = data.strip()
        if not s:
            return
        self.text.append(s + " ")
        self._chars += len(s) + 1
        if self._href is not None:
            self._link_text.append(s)
        if self._heading is not None:
            self._heading_text.append(s)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (inventory-builder)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--page-id", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--label", default=None, help="human label, e.g. 'Infobric homepage'")
    ap.add_argument("--out", default="application/task-templates/web_infobric-audit-v2/pages")
    args = ap.parse_args(argv)

    raw = fetch(args.url)
    ex = _Extract()
    ex.feed(raw)
    text = html.unescape("".join(ex.text))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    total = max(len(text), 1)

    def pos(offset: int) -> str:
        share = offset / total
        return "top" if share < 0.2 else "middle" if share < 0.65 else "bottom"

    sections = [{"name": t[:80], "level": tag, "position": pos(off)} for tag, t, off in ex.headings]
    ctas = []
    seen = set()
    for t, href in ex.links:
        low = t.lower()
        if any(w in low for w in CTA_WORDS) and (t, href) not in seen and len(t) <= 60:
            seen.add((t, href))
            ctas.append({"label": t, "href": href})
    claims = []
    for sent in re.split(r"(?<=[.!?])\s+|\n", text):
        s = sent.strip()
        if re.search(r"\d", s) and 15 <= len(s) <= 200:
            claims.append(s)
    trust = []
    low = text.lower()
    if re.search(r"\d[\d\s]{2,}\s*(kunder|användare|customers|users)", low):
        trust.append("customer_count")
    if re.search(r"kundcase|kundberättelse|case", low):
        trust.append("case_studies")
    if re.search(r"”|\"[^\"]{40,}\"|säger", low):
        trust.append("testimonial")
    if re.search(r"iso\s?\d|certifi", low):
        trust.append("certifications")
    trust.append("logos")  # almost always present as images; confirm by eye

    draft = {
        "page_id": args.page_id,
        "label": args.label or args.page_id,
        "url": args.url,
        "checked": dt.date.today().isoformat(),
        "checked_by": "DRAFT - confirm by eye and replace this value with your name",
        "truth_statement": "FILL IN: what this page/product actually is, 1-2 sentences",
        "primary_cta": {"label": ctas[0]["label"] if ctas else "FILL IN", "url_fragment": "FILL IN"},
        "secondary_ctas": [{"label": c["label"], "url_fragment": c["href"]} for c in ctas[1:8]],
        "available_next_steps": ["learn_more", "come_back_later", "leave"],
        "conversion_next_steps": [],
        "navigation_next_steps": ["learn_more"],
        "claims": claims[:12],
        "sections": sections[:30],
        "trust_signals_present": sorted(set(trust)),
        "shows_price": bool(re.search(r"\d+\s*(kr|sek)\b", low)),
        "cta_candidates_found": ctas[:20],
        "text_snapshot": text[:40000],
    }
    out = Path(args.out) / f"{args.page_id}.inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote draft {out}")
    print(f"  text: {len(text)} chars | headings: {len(sections)} | CTA candidates: {len(ctas)} | claim candidates: {len(claims)}")
    print("  CTA candidates:")
    for c in ctas[:12]:
        print(f"    - {c['label']!r} -> {c['href']}")
    print("  claim candidates:")
    for c in claims[:8]:
        print(f"    - {c[:110]}")
    print("Now confirm by eye: truth_statement, primary_cta, next_step sets, claims, trust signals, checked_by.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
