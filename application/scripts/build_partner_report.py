#!/usr/bin/env python3
"""Build the partner report for a page-audit v2 job from *every* trial.

The Playground's own text summaries send at most two 400-character snippets per
visitor kind to the model, which is fine for a smoke run and useless for a
1,000-persona study. This script instead reads all of it:

  map      every trial's four composed texts (takeaway, findings, CTA, changes) are
           read in chunks per visitor kind; the model extracts themes with counts
           and page wording quoted verbatim
  reduce   chunk outputs per (text, visitor kind) are merged - counts summed, quotes
           kept exact, at most six items per list
  count    the structured fields are counted directly, no model involved: scores,
           exit rate, next steps, missing information, most-flagged wording
  synth    one call per page turns the reduced themes plus the hard counts into the
           brief's closing sections: audience differences, journey, priorities, keep

and writes <job>/report/partner_report.md (+ .json, + ablation_summary.md via
ablation/summarize_run.py). Evidence layers are labelled the way the Main Brief asks:
[site] visible on the website · [analytics] supported by the supplied analytics ·
[persona] modelled persona interpretation. Every model call is cached under
<job>/report/cache by prompt hash, so re-running after a retry only redoes what changed.

    python application/scripts/build_partner_report.py jobs/<job-dir> [--workers 4]
        [--chunk 25] [--max-chunks N] [--model gpt-5.6-luna] [--out DIR]
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ablation"))
import summarize_run as sr  # noqa: E402  (ablation/summarize_run.py)

TEXT_FACETS = {"takeaway": "takeaway_text", "findings": "findings_text", "cta": "cta_text", "changes": "changes_text"}
DIMS = sr.DIMS
EXTRA = sr.EXTRA_SCORES
PAGE_TITLES = {"homepage": "Infobric homepage (infobric.com/se)", "fleet": "Infobric Fleet", "driving_log": "Electronic driving log",
               "equipment": "Infobric Equipment", "hyrma": "Hyrma"}
ANCHORS = {
    "understanding": ("I still could not say what they sell", "I know the category, but not what it would do for me", "I could explain to a colleague what it does and for whom"),
    "language_relevance": ("written for someone else; nothing from my world", "general business language with some familiar examples", "my situations and my words; I recognised my own problems"),
    "practical_value": ("no idea what would change in my day", "a plausible benefit, not concrete", "I can name what would get easier or cheaper for me"),
    "trust": ("I would not share my data with them", "a credible company, but the claims are unproven for my case", "I would put my own operation on it without asking for references"),
    "next_step_confidence": ("no idea what I should do next or what would happen", "I see a button but not what follows", "I know exactly what happens after clicking, and it suits me"),
    "next_step_ease": ("the step is unclear, demanding or off-putting", "doable, with some friction or uncertainty", "quick and obvious, nothing in the way"),
}
DIM_TITLES = {"understanding": "Product or company understanding", "language_relevance": "Language and relevance", "practical_value": "Perceived practical value",
              "trust": "Trust", "next_step_confidence": "Confidence in the next step", "next_step_ease": "Ease of completing that step",
              "cta_match": "Button matched expectation", "contact_likelihood": "Likelihood of contacting within a week"}

# ----------------------------------------------------------------------------- prompts

SYSTEM = (
    "You are analysing notes written by simulated website visitors (personas) for a website owner. "
    "Work only from the notes given. Wording in quotation marks or after a [position/kind] tag is text the "
    "visitor quoted from the website: keep it exactly as written, in Swedish, never translate or paraphrase it, "
    "never invent wording. Everything else in the notes is the visitor's own interpretation. Counts must never "
    "exceed the number of notes you were given. Write all of your own prose in English (titles, themes, summaries, "
    "hypotheses, checks); only the quoted page wording stays in Swedish. Return strict JSON only."
)

MAP_SCHEMAS = {
    "takeaway": """{
  "what_it_does": [{"theme": "<what these visitors concluded the company/product does and for whom, incl. where vague or wrong>", "count": <int>, "example": "<one short paraphrase>"}],
  "problems_recognised": [{"theme": "<own problem or goal recognised on the page>", "count": <int>}],
  "kept_reading_because": [{"theme": "<what on the first screen decided it>", "count": <int>, "quote": "<exact page wording if the note quotes it, else empty>"}],
  "next_step_reasons": [{"next_step": "<contact_sales|book_demo|learn_more|come_back_later|leave>", "theme": "<why>", "count": <int>}],
  "values_but_not_ready": {"count": <int>, "what_they_need_first": [{"need": "<e.g. references, price, pilot>", "count": <int>}]}
}""",
    "findings": """{
  "findings": [{"title": "<short finding>", "exact_wording": ["<page wording quoted verbatim, Swedish>"], "position": "<top|middle|bottom|mixed>",
                "creates": "<confusion|doubt|hesitation|irrelevance|missing>", "count": <int>, "who": "<who it affects and why>", "persona_interpretation": "<one sentence>"}],
  "claims_need_proof": [{"quote": "<verbatim>", "count": <int>, "proof_wanted": "<kind of proof>"}],
  "claims_credible": [{"quote": "<verbatim>", "count": <int>}],
  "language_felt_off": [{"quote": "<verbatim>", "count": <int>, "why": "<why it felt written for someone else>"}],
  "language_felt_familiar": [{"quote": "<verbatim>", "count": <int>}],
  "hesitation_reasons": [{"theme": "<what would make them hesitate or leave>", "count": <int>}]
}""",
    "cta": """{
  "button_seen": [{"label": "<button label as quoted>", "count": <int>}],
  "expected": [{"theme": "<what they expected the button to lead to>", "count": <int>}],
  "found": [{"theme": "<what actually followed, incl. what the form asks for>", "count": <int>}],
  "gaps": [{"gap": "<where reality fell short of or exceeded the expectation>", "count": <int>, "example": "<short>"}],
  "not_inspected": <int>
}""",
    "changes": """{
  "changes": [{"title": "<imperative change>", "count": <int>, "representative_quote": "<one visitor's suggestion, short, verbatim from the notes>", "how_to_check": "<visitor's own check>"}],
  "keep": [{"element": "<what already works and should stay, name the element>", "count": <int>}]
}""",
}

MAP_TASKS = {
    "takeaway": "These notes answer: what does the visitor think the company/product does; do they recognise their own problems or goals; what kept them reading; what would they do next and why. Cluster them.",
    "findings": "These notes list what visitors found confusing, missing, unconvincing or irrelevant (with [position/kind] tags), claims they would not accept without proof, claims they found credible, wording that felt written for someone else, wording that felt familiar, and what would make them hesitate or leave. Cluster them, most frequent first; keep every quoted wording exact.",
    "cta": "These notes describe the page's primary button: what the visitor expected it to lead to and what actually followed after clicking it, including what the form asks for. Cluster expectation, reality, and the gaps between them.",
    "changes": "These notes are the visitors' suggested improvements, how the website owner could check whether each helped, and what already works and should be kept. Cluster the changes into concrete themes, most frequent first.",
}


REQUIRED_KEYS = {
    "takeaway": ("what_it_does", "next_step_reasons"),
    "findings": ("findings", "claims_need_proof"),
    "cta": ("expected", "found"),
    "changes": ("changes", "keep"),
}


def map_prompt(kind: str, audience: str, notes: list[str], next_steps: list[str] | None = None) -> str:
    body = "\n\n".join(f"### Note {i + 1}\n{n}" for i, n in enumerate(notes))
    schema = MAP_SCHEMAS[kind]
    if kind == "takeaway" and next_steps:
        schema = schema.replace("<contact_sales|book_demo|learn_more|come_back_later|leave>", "<" + "|".join(next_steps) + ">")
    return (
        f"Visitor kind: {audience}. Number of notes: {len(notes)}.\n{MAP_TASKS[kind]}\n"
        f"Return JSON with exactly this shape (at most 6 items per list, counts are numbers of notes, <= {len(notes)}):\n{schema}\n\n{body}"
    )


def reduce_prompt(kind: str, audience: str, parts: list[dict], total: int) -> str:
    return (
        f"Visitor kind: {audience}. Below are {len(parts)} partial analyses of the same kind of notes, covering {total} notes in total. "
        f"Merge them into one analysis of exactly the same JSON shape: combine items that mean the same thing, sum their counts "
        f"(never exceeding {total}), keep at most 6 items per list ordered by count, keep every quoted page wording exactly as given "
        f"and drop duplicates. Do not add anything that is not in the partial analyses.\n\nShape:\n{MAP_SCHEMAS[kind]}\n\n"
        + "\n\n".join(f"### Partial {i + 1}\n{json.dumps(p, ensure_ascii=False)}" for i, p in enumerate(parts))
    )


SYNTH_SCHEMA = """{
  "executive_summary": ["<3-5 sentences, each a distinct conclusion, each tagged [persona] or [site] or [analytics]>"],
  "audience_differences": [{"audience": "<visitor kind>", "summary": "<2-3 sentences: what they understood, what they valued, what held them back, incl. the case of understanding and valuing the offer but not being ready to make contact and what they would need first>"}],
  "journey": {
    "information_order": "<does the information appear in a useful order>",
    "answers_when_questions_arise": "<can visitors find answers when questions arise>",
    "how_it_works_in_practice": "<is it clear how the product works in practice>",
    "interested_but_not_ready": "<does the experience help someone interested but not ready to speak to sales>",
    "layout_navigation_forms": "<are layout, navigation, buttons and forms easy to understand and use>",
    "unnecessary_effort_or_uncertainty": "<where the experience creates unnecessary effort or uncertainty>"
  },
  "priorities": [{"rank": <1-5>, "title": "<imperative>", "hypothesis": "<what would change for whom and why>", "evidence": "<the finding(s) and counts it rests on, quoting exact wording where available>", "affects": "<visitor kinds>", "how_to_check": "<a measurable check, using the analytics where possible>"}],
  "retain": [{"element": "<what already works>", "why": "<evidence>"}],
  "trust_advice": {
    "where_trust_stops": "<from the ladder: which commitment prospects accept and where they stop, with counts>",
    "what_would_move_the_next_rung": ["<concrete things, from the visitors' own words, that would make them accept the next commitment>"],
    "claims": [{"quote": "<verbatim>", "status": "<believed|doubted|mixed>", "what_proof": "<what would make it believable>"}],
    "advice": ["<3-5 imperative, page-specific changes to earn trust, each tagged [persona] or [site]>"]
  },
  "cannot_be_assessed": ["<anything the pilot could not assess and why>"]
}"""


TRUST_SCHEMA = """{
  "where_trust_stops": "<2 sentences: from the ladder, which commitment prospects accept and where they stop, with the counts>",
  "what_would_move_the_next_rung": ["<3-6 concrete things, in the visitors' own terms, that would make them accept the next commitment>"],
  "claims": [{"quote": "<verbatim page wording>", "status": "<believed|doubted|mixed>", "what_proof": "<what would make it believable, from the notes>"}],
  "advice": ["<3-5 imperative, page-specific changes to earn trust, each starting with [site] or [persona]>"]
}"""


def trust_prompt(page_title: str, trust: dict, wording: dict, reduced_findings: dict) -> str:
    claims = {"believed": (wording.get("claims_credible") or {}).get("items", [])[:6],
              "doubted": (wording.get("claims_need_proof") or {}).get("items", [])[:8]}
    per_kind = {aud: {"claims_need_proof": (r.get("claims_need_proof") or [])[:5], "hesitation_reasons": (r.get("hesitation_reasons") or [])[:5]}
                for aud, r in (reduced_findings or {}).items()}
    return (
        f"Page: {page_title}. Write the trust section of a website persona-study report for the website owner, from the evidence below only. "
        "The ladder is four commitments of rising cost (work email for a guide < call-back < demo this week < pilot on own data), answered by prospects; "
        "the claim item is belief, not a commitment. Quote page wording verbatim in Swedish. Counts as 'N of M'. Tag advice [site] (visible on the site) "
        f"or [persona] (interpretation).\n\nShape:\n{TRUST_SCHEMA}\n\n### Ladder and needs (prospects)\n{json.dumps(trust, ensure_ascii=False)}\n\n"
        f"### Claims believed / doubted (exact counts)\n{json.dumps(claims, ensure_ascii=False)}\n\n### Per visitor kind: doubted claims with the proof wanted, hesitation reasons\n{json.dumps(per_kind, ensure_ascii=False)}"
    )


def synth_prompt(page_title: str, reduced: dict, hard: dict, analytics: dict) -> str:
    return (
        f"Page: {page_title}. You are writing the closing sections of a website persona-study report for the website owner. "
        "Below are (A) per-visitor-kind analyses of the visitors' notes, (B) hard counts computed directly from their structured answers, "
        "and (C) the owner's own web analytics for this page over 90 days. Write the sections in the JSON shape given. Be concrete: name "
        "sections and quote exact wording (Swedish, verbatim) where the analyses provide it; give counts as 'about N of M visitors'. "
        "Tag each statement's evidence layer: [site] for what is visible on the website, [analytics] for what the supplied analytics support, "
        "[persona] for modelled persona interpretation. Persona scores are indicators for this pilot, not measured customer approval. "
        f"Give 3-5 priorities ordered by impact. For trust_advice use (B).trust: the ladder of commitments (email for a guide < call-back < demo < pilot), "
        "the claim item, what visitors need before going further, the information they missed, the claims they doubted and the proof they wanted, "
        "and their own ladder reasons where present.\n\nShape:\n{SYNTH_SCHEMA}\n\n"
        f"### (A) per visitor kind\n{json.dumps(reduced, ensure_ascii=False)}\n\n### (B) hard counts\n{json.dumps(hard, ensure_ascii=False)}\n\n"
        f"### (C) analytics\n{json.dumps(analytics, ensure_ascii=False)}"
    )


# ----------------------------------------------------------------------------- model + cache

class Model:
    def __init__(self, model: str, cache_dir: Path):
        import openai

        sr_env = REPO / "application" / "playground" / ".env.local"
        for line in (sr_env.read_text().splitlines() if sr_env.is_file() else []):
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        self.client = openai.OpenAI(base_url=os.environ["OPENAI_BASE_URL"], api_key=os.environ["OPENAI_API_KEY"], timeout=240)
        self.model = model
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0
        self.cached = 0
        self.tokens = [0, 0]

    def json(self, user: str, max_tokens: int, tag: str, required: tuple[str, ...] = ()) -> dict:
        key = hashlib.sha256((self.model + "\n" + SYSTEM + "\n" + user).encode("utf-8")).hexdigest()[:20]
        path = self.cache_dir / f"{tag}-{key}.json"
        if path.is_file():
            cached = json.loads(path.read_text())["result"]
            if all(k in cached for k in required):
                self.cached += 1
                return cached
        delay = 4.0
        last = None
        budget = max_tokens
        for attempt in range(6):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                    response_format={"type": "json_object"},
                    max_completion_tokens=budget,
                )
                self.calls += 1
                self.tokens[0] += resp.usage.prompt_tokens
                self.tokens[1] += resp.usage.completion_tokens
                result = json.loads(resp.choices[0].message.content or "{}")
                missing = [k for k in required if k not in result]
                if missing and (attempt < 2 and budget < 100_000):
                    # Reasoning tokens count against the budget; an exhausted budget comes
                    # back as an empty or partial object. Try again with more room, twice.
                    last = RuntimeError(f"missing keys {missing} (budget {budget})")
                    budget = min(int(budget * 2), 100_000)
                    continue
                if missing:
                    # Keep what came back rather than fail the whole report; the caller
                    # renders absent sections as absent.
                    sys.stderr.write(f"  {tag}: keys still missing after retries: {missing} - continuing with partial result\n")
                    for k in missing:
                        result[k] = {} if k in ("journey", "trust_advice") else []
                path.write_text(json.dumps({"tag": tag, "model": self.model, "usage": [resp.usage.prompt_tokens, resp.usage.completion_tokens],
                                            "prompt_chars": len(user), "result": result}, ensure_ascii=False, indent=1))
                return result
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(delay)
                delay = min(delay * 2, 90)
        raise RuntimeError(f"{tag}: model failed: {last!r}")


# ----------------------------------------------------------------------------- inputs

def load_texts(job: Path) -> list[dict]:
    """One row per passed trial: persona dims + the four composed texts + raw quote lists."""
    rows = []
    for so_path in sorted(job.glob("*/verifier/structured_output.json")):
        trial = so_path.parent.parent
        q_path = so_path.parent / "quality.json"
        raw_path = trial / "artifacts" / "app" / "output" / "page_audit.json"
        if not q_path.is_file():
            continue
        q = json.loads(q_path.read_text())
        so = json.loads(so_path.read_text())
        texts = {}
        for c in so.get("contexts") or []:
            for f in c.get("facets") or []:
                for short, key in TEXT_FACETS.items():
                    if f.get("key") == key and isinstance(f.get("value"), str):
                        texts[short] = f["value"]
        raw = {}
        if raw_path.is_file():
            try:
                raw = json.loads(raw_path.read_text(encoding="utf-8", errors="replace"))
            except json.JSONDecodeError:
                raw = {}
        seg = str((q.get("persona") or {}).get("traffic_segment") or "Prospect (evaluating a supplier)").split(" (")[0]
        rows.append({"trial": trial.name, "audience": (q.get("persona") or {}).get("audience_group") or "unknown", "quality": q,
                     "texts": texts, "raw": raw, "segment": seg, "stayed": not (q.get("exit") or {}).get("left_early"),
                     "next_step": (q.get("decision") or {}).get("next_step"), "prospect": seg == "Prospect",
                     "intent": (q.get("persona") or {}).get("visit_intent")})
    return rows


LADDER = ["trust_email_guide", "trust_callback", "trust_demo_week", "trust_pilot_data"]
LADDER_TITLES = {"trust_email_guide": "give a work email for a guide", "trust_callback": "ask for a call-back",
                 "trust_demo_week": "book a demo this week", "trust_pilot_data": "run a pilot on own data this month"}


def prospect_scores(pros: list[dict]) -> dict:
    out = {}
    for k in DIMS + EXTRA:
        vals = [r["quality"]["scores_in_browse"].get(k) for r in pros]
        vals = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        m = statistics.mean(vals) if vals else None
        sd = statistics.pstdev(vals) if len(vals) > 1 else None
        out[k] = {"n": len(vals), "mean": m, "sd": sd, "dist": {str(i): sum(1 for v in vals if int(v) == i) for i in range(1, 6)}}
    return out


ELSEWHERE = ("go_to_login", "go_elsewhere_on_site")


def exits_by_segment(rows: list[dict]) -> dict:
    """Three mutually exclusive outcomes of the first screen, plus what the readers do next.

    bounced  left the site after the first screen           -> the counterpart of a Quick Back
    routed   went to login or another page without reading  -> a normal journey, invisible to Quick Backs
    stayed   read the page                                  -> of whom `then_elsewhere` would go on to
                                                               another page of the site, which is interest,
                                                               not traffic leaking away
    """
    out = {}
    for seg in [s for s, _ in collections.Counter(r["segment"] for r in rows).most_common()]:
        sub = [r for r in rows if r["segment"] == seg]
        left = [r for r in sub if not r["stayed"]]
        stayed = [r for r in sub if r["stayed"]]
        out[seg] = {
            "n": len(sub),
            "bounced": sum(1 for r in left if r["next_step"] not in ELSEWHERE),
            "routed": sum(1 for r in left if r["next_step"] in ELSEWHERE),
            "stayed": len(stayed),
            "then_elsewhere": sum(1 for r in stayed if r["next_step"] in ELSEWHERE),
        }
    return out


def trust_block(pros: list[dict], rows: list[dict]) -> dict:
    """Everything the report says about trust, computed from the structured answers."""
    def yes(sub, k):
        return sum(1 for r in sub if r["quality"]["scores_in_browse"].get(k) == "yes")
    ladder = {k: {"yes": yes(pros, k), "n": len(pros)} for k in LADDER + ["trust_claim_unchecked"]}
    counts = [r["quality"]["scores_in_browse"].get("trust_ladder") for r in pros]
    counts = [c for c in counts if isinstance(c, int)]
    by_intent = {}
    for intent in {r["intent"] for r in pros}:
        sub = [r for r in pros if r["intent"] == intent]
        by_intent[str(intent)] = {"n": len(sub), **{k: yes(sub, k) for k in LADDER}}
    reasons = [str(r["raw"].get("trust_ladder_reason")) for r in pros if r["raw"].get("trust_ladder_reason") not in (None, "", "unknown")]
    return {
        "ladder": ladder,
        "rungs_distribution": {str(i): sum(1 for c in counts if c == i) for i in range(5)} if counts else {},
        "rungs_mean": statistics.mean(counts) if counts else None,
        "by_intent": by_intent,
        "trust_action": dict(collections.Counter(r["quality"]["decision"].get("trust_action") for r in pros)),
        "missing_info": dict(collections.Counter(m for r in pros for m in (r["quality"].get("missing_info") or []))),
        "trust_score_1_5": prospect_scores(pros).get("trust"),
        "ladder_reasons_sample": reasons[:12],
        "all_segments_claim_unchecked": {"yes": yes(rows, "trust_claim_unchecked"), "n": len(rows)},
    }


def page_facts(job: Path) -> dict:
    """The page's own vocabulary, read from the task the job ran: the next steps that
    exist on this page (so the narrative is not bucketed into another page's options)
    and the proof claim the trust question actually named."""
    facts = {"next_steps": [], "proof_claim": None}
    try:
        cfg = json.loads((job / "config.json").read_text())
        rel = (cfg.get("datasets") or cfg.get("tasks") or [{}])[0].get("path") or ""
        task = REPO / rel
        inv = json.loads((task / "input" / "inventory.json").read_text())
        facts["next_steps"] = [str(v) for v in (inv.get("available_next_steps") or [])]
        m = re.search(r"Proof claim[^«]*«(.+?)»", (task / "instruction.md").read_text())
        if m:
            facts["proof_claim"] = m.group(1).strip()
    except Exception:  # noqa: BLE001
        pass
    return facts


def norm_quote(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().strip(".,;:!?»«\"'”“ ").lower()


def most_flagged_wording(rows: list[dict]) -> dict[str, list[dict]]:
    """Exact-string counts of quoted page wording, per raw field, with per-audience breakdown."""
    out = {}
    fields = {"claims_need_proof": "Claims visitors wanted proof for", "language_felt_off": "Wording that felt written for someone else",
              "claims_credible": "Claims visitors found credible", "language_felt_familiar": "Wording that felt like the visitor's own world"}
    for field, title in fields.items():
        counter: dict[str, dict] = {}
        for r in rows:
            vals = r["raw"].get(field) or []
            seen = set()
            for v in vals if isinstance(vals, list) else []:
                key = norm_quote(v if isinstance(v, str) else json.dumps(v))
                if not key or key in seen:
                    continue
                seen.add(key)
                entry = counter.setdefault(key, {"quote": str(v).strip(), "count": 0, "by_audience": collections.Counter()})
                entry["count"] += 1
                entry["by_audience"][r["audience"]] += 1
        ranked = sorted(counter.values(), key=lambda e: -e["count"])[:12]
        out[field] = {"title": title, "items": [{"quote": e["quote"], "count": e["count"], "by_audience": dict(e["by_audience"])} for e in ranked]}
    # confusing_or_missing carries position/kind
    counter = {}
    for r in rows:
        for item in r["raw"].get("confusing_or_missing") or []:
            if not isinstance(item, dict):
                continue
            key = norm_quote(item.get("what"))
            if not key:
                continue
            e = counter.setdefault(key, {"what": str(item.get("what")).strip(), "count": 0, "where": collections.Counter(), "kind": collections.Counter(), "by_audience": collections.Counter()})
            e["count"] += 1
            e["where"][str(item.get("where"))] += 1
            e["kind"][str(item.get("kind"))] += 1
            e["by_audience"][r["audience"]] += 1
    ranked = sorted(counter.values(), key=lambda e: -e["count"])[:15]
    out["confusing_or_missing"] = {"title": "What was flagged as confusing, missing, unconvincing or irrelevant (exact entries)",
                                   "items": [{"what": e["what"], "count": e["count"], "where": e["where"].most_common(1)[0][0], "kind": e["kind"].most_common(1)[0][0],
                                              "by_audience": dict(e["by_audience"])} for e in ranked]}
    return out


# ----------------------------------------------------------------------------- pipeline

def run_map_reduce(model: Model, rows: list[dict], chunk: int, workers: int, max_chunks: int, next_steps: list[str] | None = None) -> dict:
    """{kind: {audience: reduced_json}}"""
    by_aud: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_aud[r["audience"]].append(r)
    jobs = []
    for kind in TEXT_FACETS:
        for aud, group in by_aud.items():
            notes = [r["texts"][kind] for r in group if r["texts"].get(kind)]
            chunks = [notes[i : i + chunk] for i in range(0, len(notes), chunk)]
            if max_chunks:
                chunks = chunks[:max_chunks]
            for ci, ch in enumerate(chunks):
                jobs.append((kind, aud, ci, ch))
    sys.stderr.write(f"map: {len(jobs)} chunks over {len(rows)} trials ({len(by_aud)} visitor kinds)\n")
    partials: dict[tuple[str, str], list[tuple[int, dict, int]]] = collections.defaultdict(list)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(model.json, map_prompt(k, a, ch, next_steps), 6000, f"map-{k}", REQUIRED_KEYS[k]): (k, a, ci, len(ch)) for k, a, ci, ch in jobs}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            k, a, ci, n = futs[fut]
            partials[(k, a)].append((ci, fut.result(), n))
            done += 1
            if done % 20 == 0 or done == len(futs):
                sys.stderr.write(f"  map {done}/{len(futs)} (calls {model.calls}, cached {model.cached})\n")
    reduced: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    red_jobs = []
    for (k, a), parts in partials.items():
        parts.sort()
        total = sum(n for _, _, n in parts)
        if len(parts) == 1:
            reduced[k][a] = {"_n": total, **parts[0][1]}
        else:
            red_jobs.append((k, a, [p for _, p, _ in parts], total))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(model.json, reduce_prompt(k, a, ps, t), 7000, f"reduce-{k}", REQUIRED_KEYS[k]): (k, a, t) for k, a, ps, t in red_jobs}
        for fut in concurrent.futures.as_completed(futs):
            k, a, t = futs[fut]
            reduced[k][a] = {"_n": t, **fut.result()}
    sys.stderr.write(f"reduce: {len(red_jobs)} merges done (calls {model.calls}, cached {model.cached})\n")
    return reduced


# ----------------------------------------------------------------------------- markdown

def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "n/a"


def about(n, m):
    return f"about {n} of {m}" if m else str(n)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "|".join("---" if i == 0 else "---:" for i in range(len(headers))) + "|"]
                     + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def build_markdown(page: str, job: Path, rows: list[dict], numbers: dict, reduced: dict, hard: dict, synth: dict, analytics: dict, model_name: str) -> str:
    title = PAGE_TITLES.get(page, page)
    n = len(rows)
    groups = [g for g, _ in collections.Counter(r["audience"] for r in rows).most_common()]
    o = []
    w = o.append
    w(f"# {title} — persona study pilot, page report\n")
    vs = sorted({str((r.get("quality") or {}).get("instrument_version") or "") for r in rows} - {""})
    w(f"*{n} simulated visitors (personas) · {dt.date.today().isoformat()} · run `{job.name}` · model {model_name} · "
      f"instrument v{', v'.join(vs) if vs else '?'}*\n")
    w("**How to read this report.** Each statement carries its evidence layer: **[site]** visible on the website · **[analytics]** supported by the "
      "supplied 90-day analytics · **[persona]** modelled persona interpretation. Persona scores are indicators for this pilot, not measured customer "
      "approval or conversion forecasts. Page wording is quoted exactly as written, in Swedish. Counts from the visitors' structured answers are exact; "
      "counts inside the theme tables were clustered by the model from the visitors' free-text notes and are approximate.\n")

    # --- executive summary
    w("## Summary\n")
    for s in synth.get("executive_summary") or []:
        w(f"- {s}")
    w("")

    # --- 1 compact overview
    w("## 1. Compact overview\n")
    np_, nr = hard.get("n_prospects", n), hard.get("n_read_page", n)
    w(f"**Who this section is about.** {n} simulated visitors in total; the six dimensions below are answered by the **{np_} prospects** "
      f"(people evaluating a supplier), because existing customers and visitors who arrived by mistake do not judge the offer. "
      f"Sections 2–7 are written from the {nr} visitors who read the page. Exits are reported for everyone, by segment, in this section.\n")
    w("Scores are 1–5. Two readings per dimension: **in-browse** (given at the end of the visit) and **scored after the visit** (the same persona "
      "re-rates from its own notes, away from the browser; see §9 for why both are shown).\n")
    sc, ph = hard.get("scores") or numbers.get("scores", {}), numbers.get("post_hoc", {})
    scored_by_g = numbers.get("scores_by_audience_scored") or {}
    have_scored = any(isinstance(v.get(k), (int, float)) for v in scored_by_g.values() for k in DIMS)
    by_g_src = scored_by_g if have_scored else (hard.get("scores_by_audience") or {})
    groups_shown = [g for g in groups if g in by_g_src]
    hdr = ["Dimension", "mean in-browse", "spread (sd)"] + (["mean scored", "spread (sd, scored)"] if have_scored else []) + groups_shown
    body = []
    for k in DIMS:
        row = [DIM_TITLES[k], fmt(sc.get(k, {}).get("mean")), fmt(sc.get(k, {}).get("sd"))]
        if have_scored:
            row += [fmt(ph.get(k, {}).get("mean_scored")), fmt(ph.get(k, {}).get("sd_scored"))]
        row += [fmt(by_g_src.get(g, {}).get(k)) for g in groups_shown]
        body.append(row)
    w(md_table(hdr, body))
    w("\n*Per-visitor-kind columns show the " + ("scored-after-the-visit" if have_scored else "in-browse") + " mean for prospects of that kind.*\n")
    w("**What the scores mean (anchors given to every persona):**\n")
    for k, (a1, a3, a5) in ANCHORS.items():
        w(f"- **{DIM_TITLES[k]}** — 1: {a1}. 3: {a3}. 5: {a5}.")
    w("")
    cna = synth.get("cannot_be_assessed") or []
    w("**Cannot be assessed / read with care:**" + ("" if cna else " nothing was excluded; see §9 for limits.") + "\n")
    for c in cna:
        w(f"- {c}")
    w("")
    ex = numbers.get("exit_rate")
    w(f"- **Stayed or left [persona]:** {pct(round((ex or 0) * n), n)} of visitors left after the first screen; the rest kept reading. "
      f"[analytics] Clarity records {fmt(analytics.get('clarity', {}).get('quick_backs'), 3)} Quick Backs on this page (a real session that left within seconds) — see §8.")
    exits = hard.get("exits") or {}
    if exits:
        w("\n**What the first screen decided, by traffic segment** [persona]. The three outcomes are exclusive and add to 100%. "
          "*Bounced* = left the site after the first screen, the counterpart of a Quick Back. *Routed* = went to login or another page "
          "without reading, a normal journey the Quick Back figure never counts. *Stayed* = read the page; the last column is the share "
          "of those readers whose next step is another page of this site, which is interest, not traffic lost.\n")
        w(md_table(["Traffic segment", "n", "bounced", "routed", "stayed", "of readers: on to another page"],
                   [[seg, v["n"], pct(v["bounced"], v["n"]), pct(v["routed"], v["n"]), pct(v["stayed"], v["n"]),
                     pct(v["then_elsewhere"], v["stayed"]) if v["stayed"] else "n/a"] for seg, v in exits.items()]))
        w("")
    tr = hard.get("trust") or {}
    if tr.get("ladder"):
        w("**Trust as commitments [persona], prospects only.** Each question is a real commitment with a cost; the ladder shows where trust stops.\n")
        lad = tr["ladder"]
        w(md_table(["Would they…", "yes"], [[LADDER_TITLES[k], pct(lad[k]["yes"], lad[k]["n"]) + f" of {lad[k]['n']}"] for k in LADDER]
                   + [[f"accept «{(hard.get('page_facts') or {}).get('proof_claim') or 'the page-brief proof claim'}» without checking (belief, not a commitment)",
                        pct(lad["trust_claim_unchecked"]["yes"], lad["trust_claim_unchecked"]["n"])]]))
        dist = tr.get("rungs_distribution") or {}
        if dist:
            w(f"\nCommitments accepted per prospect: " + ", ".join(f"{k}: {v}" for k, v in dist.items()) + f" (mean {fmt(tr.get('rungs_mean'))}). ")
        bi = tr.get("by_intent") or {}
        if len(bi) > 1:
            w("By reason for visiting: " + "; ".join(f"{intent} (n={v['n']}): " + ", ".join(f"{LADDER_TITLES[k].split(' ')[0]} {pct(v[k], v['n'])}" for k in LADDER) for intent, v in bi.items()) + ".")
        w("")
    ns = numbers.get("next_step") or {}
    w(f"- **Next step [persona]:** " + "; ".join(f"{k} {v} ({pct(v, n)})" for k, v in sorted(ns.items(), key=lambda kv: -kv[1])))
    ta = numbers.get("trust_action") or {}
    w(f"- **Needed before going further [persona]:** " + "; ".join(f"{k} {v} ({pct(v, n)})" for k, v in sorted(ta.items(), key=lambda kv: -kv[1])))
    w(f"- **Likelihood of contacting within a week [persona]:** mean {fmt(sc.get('contact_likelihood', {}).get('mean'))} (1–5), "
      f"distribution " + ", ".join(f"{i}: {sc.get('contact_likelihood', {}).get('dist', {}).get(str(i), 0)}" for i in range(1, 6)))
    w("")

    # --- 2 understanding per audience
    w("## 2. What visitors think the company does, and whether they recognise themselves\n")
    w("*Brief §5: what does the visitor think the product or company does; do they recognise their own problems or goals; what kept them reading; what would they do next.* All [persona] unless quoted.\n")
    for g in groups:
        r = (reduced.get("takeaway") or {}).get(g)
        if not r:
            continue
        m = r.get("_n", 0)
        w(f"### {g} ({m} visitors)\n")
        for it in (r.get("what_it_does") or [])[:4]:
            w(f"- **Understood it as:** {it.get('theme')} — {about(it.get('count', 0), m)}.")
        pr = r.get("problems_recognised") or []
        if pr:
            w("- **Own problems recognised:** " + "; ".join(f"{it.get('theme')} ({it.get('count')})" for it in pr[:5]))
        kr = r.get("kept_reading_because") or []
        if kr:
            w("- **Kept reading because:** " + "; ".join(f"{it.get('theme')} ({it.get('count')})" + (f" — [site] «{it.get('quote')}»" if it.get("quote") else "") for it in kr[:4]))
        nx = r.get("next_step_reasons") or []
        if nx:
            w("- **Next step and why:** " + "; ".join(f"{it.get('next_step')}: {it.get('theme')} ({it.get('count')})" for it in nx[:5]))
        vb = r.get("values_but_not_ready") or {}
        if vb.get("count"):
            w(f"- **Understood and valued the offer but not ready to make contact:** {about(vb.get('count'), m)}; would need first: "
              + "; ".join(f"{it.get('need')} ({it.get('count')})" for it in (vb.get("what_they_need_first") or [])[:4]))
        w("")

    # --- 3 findings
    w("## 3. Findings: exact wording, who it affects, what it creates\n")
    w("### 3a. Most-flagged wording (exact counts from the visitors' structured answers)\n")
    for field in ("confusing_or_missing", "claims_need_proof", "language_felt_off", "claims_credible", "language_felt_familiar"):
        block = hard["wording"].get(field)
        if not block or not block["items"]:
            continue
        w(f"**{block['title']}** [site wording, persona reaction]\n")
        if field == "confusing_or_missing":
            w(md_table(["Entry (as written by the visitor)", "visitors", "where", "kind", "mainly among"],
                       [[f"«{it['what'][:140]}»", it["count"], it["where"], it["kind"], max(it["by_audience"], key=it["by_audience"].get)] for it in block["items"]]))
        else:
            w(md_table(["Wording", "visitors", "mainly among"], [[f"«{it['quote'][:140]}»", it["count"], max(it["by_audience"], key=it["by_audience"].get)] for it in block["items"]]))
        w("")
    mi = numbers.get("missing_info_counts") or {}
    if mi:
        w("**Information visitors said was missing** (exact counts): " + "; ".join(f"{k} {v} ({pct(v, n)})" for k, v in sorted(mi.items(), key=lambda kv: -kv[1])[:8]) + "\n")
    w("### 3b. Findings by visitor kind (clustered from the notes)\n")
    for g in groups:
        r = (reduced.get("findings") or {}).get(g)
        if not r:
            continue
        m = r.get("_n", 0)
        w(f"### {g} ({m} visitors)\n")
        for f in (r.get("findings") or [])[:5]:
            quotes = "; ".join(f"«{q}»" for q in (f.get("exact_wording") or [])[:3])
            w(f"- **{f.get('title')}** — {about(f.get('count', 0), m)} · creates {f.get('creates')} · {f.get('position')} of the page. "
              + (f"[site] {quotes}. " if quotes else "") + f"[persona] Who: {f.get('who')} {f.get('persona_interpretation') or ''}")
        cp = r.get("claims_need_proof") or []
        if cp:
            w("- **Claims they would not accept without proof:** " + "; ".join(f"[site] «{it.get('quote')}» ({it.get('count')}) → wanted {it.get('proof_wanted')}" for it in cp[:4]))
        lo = r.get("language_felt_off") or []
        if lo:
            w("- **Wording that felt written for someone else:** " + "; ".join(f"[site] «{it.get('quote')}» ({it.get('count')}) — {it.get('why')}" for it in lo[:4]))
        hs = r.get("hesitation_reasons") or []
        if hs:
            w("- **What would make them hesitate or leave:** " + "; ".join(f"{it.get('theme')} ({it.get('count')})" for it in hs[:4]))
        w("")

    # --- 3c trust
    ta = synth.get("trust_advice") or {}
    tr = hard.get("trust") or {}
    w("### 3c. What would make them trust it\n")
    w("*Brief §5: which claims feel credible and which need proof; §7: trust. Built from the commitment ladder, what visitors said they need before going further, "
      "the information they missed, the claims they doubted, and their own words.*\n")
    if ta.get("where_trust_stops"):
        w(f"- **Where trust stops:** {ta['where_trust_stops']}")
    if tr.get("trust_action"):
        w("- **Needed before going further (prospects):** " + "; ".join(f"{k} {v}" for k, v in sorted(tr["trust_action"].items(), key=lambda kv: -kv[1])))
    if tr.get("missing_info"):
        w("- **Information they missed (prospects):** " + "; ".join(f"{k} {v}" for k, v in sorted(tr["missing_info"].items(), key=lambda kv: -kv[1])))
    cred = hard["wording"].get("claims_credible", {}).get("items") or []
    doubt = hard["wording"].get("claims_need_proof", {}).get("items") or []
    if cred:
        w("- **Believed [site wording]:** " + "; ".join(f"«{it['quote'][:80]}» ({it['count']})" for it in cred[:3]))
    if doubt:
        w("- **Doubted [site wording]:** " + "; ".join(f"«{it['quote'][:80]}» ({it['count']})" for it in doubt[:5]))
    for c in (ta.get("claims") or [])[:5]:
        w(f"  - «{c.get('quote')}» — {c.get('status')}; what would make it believable: {c.get('what_proof')}")
    if ta.get("what_would_move_the_next_rung"):
        w("- **What would move them to the next commitment [persona]:**")
        for it in ta["what_would_move_the_next_rung"][:6]:
            w(f"  - {it}")
    if tr.get("ladder_reasons_sample"):
        w("- **In their own words (why they stop where they stop):**")
        for it in tr["ladder_reasons_sample"][:6]:
            w(f"  - “{it[:220]}”")
    if ta.get("advice"):
        w("- **Advice to earn trust on this page:**")
        for it in ta["advice"][:5]:
            w(f"  - {it}")
    w("")

    # --- 4 CTA
    w("## 4. The primary button: expectation vs what followed\n")
    q = numbers.get("quality") or {}
    w(f"[site] Button inspected by {pct(round((q.get('cta_inspected') or 0) * n), n)} of visitors; reached one of the page's known destinations for {pct(round((q.get('cta_url_ok') or 0) * n), n)} "
      f"(a navigation check, not a check that it met their expectation - that is the 1-5 below). "
      f"[persona] Expectation match (1–5): mean {fmt(sc.get('cta_match', {}).get('mean'))} in-browse, {fmt(ph.get('cta_match', {}).get('mean_scored'))} scored after the visit.\n")
    for g in groups:
        r = (reduced.get("cta") or {}).get(g)
        if not r:
            continue
        m = r.get("_n", 0)
        w(f"**{g} ({m} visitors):** expected " + "; ".join(f"{it.get('theme')} ({it.get('count')})" for it in (r.get("expected") or [])[:3])
          + ". Found " + "; ".join(f"{it.get('theme')} ({it.get('count')})" for it in (r.get("found") or [])[:3])
          + ". Gaps: " + ("; ".join(f"{it.get('gap')} ({it.get('count')})" for it in (r.get("gaps") or [])[:3]) or "none reported") + ".")
    w("")

    # --- 5 audience differences
    w("## 5. Differences between visitor kinds worth preserving\n")
    for a in synth.get("audience_differences") or []:
        w(f"- **{a.get('audience')}:** {a.get('summary')}")
    w("")
    if have_scored:
        w("Scored-after-the-visit means by visitor kind:\n")
        w(md_table(["Visitor kind", "n"] + [DIM_TITLES[k] for k in DIMS + EXTRA],
                   [[g, (numbers.get("scores_by_audience") or {}).get(g, {}).get("n", "")] + [fmt(scored_by_g.get(g, {}).get(k)) for k in DIMS + EXTRA] for g in groups]))
        w("")
    exits = hard.get("exits") or {}

    # --- 6 journey
    w("## 6. Customer journey assessment (Brief §6)\n")
    jr = synth.get("journey") or {}
    for key, label in (("information_order", "Does the information appear in a useful order?"), ("answers_when_questions_arise", "Can visitors find answers when questions arise?"),
                       ("how_it_works_in_practice", "Is it clear how the product works in practice?"), ("interested_but_not_ready", "Does it help someone interested but not ready to speak to sales?"),
                       ("layout_navigation_forms", "Are layout, navigation, buttons and forms easy to understand and use?"), ("unnecessary_effort_or_uncertainty", "Where does it create unnecessary effort or uncertainty?")):
        w(f"- **{label}** {jr.get(key) or 'not assessed'}")
    w("")

    # --- 7 priorities + keep
    w("## 7. Priorities and what to keep\n")
    for p in sorted(synth.get("priorities") or [], key=lambda p: p.get("rank", 9)):
        w(f"**{p.get('rank')}. {p.get('title')}**  \n*Hypothesis:* {p.get('hypothesis')}  \n*Evidence:* {p.get('evidence')}  \n*Affects:* {p.get('affects')}  \n*How to check:* {p.get('how_to_check')}\n")
    w("**Suggested changes by visitor kind (clustered from the notes):**\n")
    for g in groups:
        r = (reduced.get("changes") or {}).get(g)
        if not r:
            continue
        w(f"- *{g}:* " + "; ".join(f"**{it.get('title')}** ({it.get('count')}) — check: {it.get('how_to_check')}" for it in (r.get("changes") or [])[:4]))
    w("\n**Keep:**\n")
    for k in synth.get("retain") or []:
        w(f"- {k.get('element')} — {k.get('why')}")
    w("")

    # --- 8 analytics
    w("## 8. What the supplied analytics say about this page (90 days) [analytics]\n")
    ga, cl, ev = analytics.get("ga4") or {}, analytics.get("clarity") or {}, analytics.get("clarity_smart_events") or {}
    w(md_table(["Measure", "Value"], [["GA4 views / sessions", f"{ga.get('views')} / {ga.get('sessions')}"], ["Engaged share (GA4)", fmt(ga.get("engaged_share"), 3)],
                                       ["Average engagement (s)", ga.get("avg_engagement_sec")], ["Scroll depth (Clarity)", fmt(cl.get("scroll_depth"), 3)],
                                       ["Quick Backs (Clarity)", f"{fmt(cl.get('quick_backs'), 3)} ({cl.get('quick_backs_sessions')} sessions)"],
                                       ["Dead / rage clicks", f"{fmt(cl.get('dead_clicks'), 3)} / {fmt(cl.get('rage_clicks'), 3)}"],
                                       ["New / returning users", f"{fmt(cl.get('new_users_share'), 2)} / {fmt(cl.get('returning_users_share'), 2)}"],
                                       ["Smart events", ", ".join(f"{k} {v}" for k, v in ev.items())]]))
    w(f"\nSide by side: [persona] {pct(round((ex or 0) * n), n)} of personas left after the first screen vs [analytics] {fmt(cl.get('quick_backs'), 3)} Quick Backs. "
      "These are not the same event (a Quick Back includes wrong clicks and bounces measured in seconds; a persona exit is a considered decision after reading the first screen), "
      "so the comparison is directional: it says whether the simulation is more or less forgiving than real traffic, not which is right.\n")
    for note in analytics.get("notes") or []:
        w(f"- {note}")
    w("")

    # --- 9 method
    w("## 9. Method, coverage and limits\n")
    w(f"- **Personas:** {n} synthetic visitors drawn proportionally from the six visitor kinds in the brief (§4) with Swedish construction-sector roles, "
      "each carrying its own reason for visiting (a specific problem today, or exploring) and prior familiarity with Infobric. They were not shown the analytics.")
    w("- **Visit:** each persona briefed itself, opened the page in a real browser, judged the first screen (with leaving as a valid outcome), read the whole page, "
      "clicked the primary button once, then answered the questionnaire and rated the six dimensions on the anchors above.")
    w(f"- **Coverage:** {numbers.get('finished')} of {numbers.get('launched')} visits completed, {numbers.get('passed')} passed the automated checks "
      f"({pct(numbers.get('passed', 0), numbers.get('finished', 1))}); persona fidelity {pct(round((q.get('fidelity_rate') or 0) * n), n)}; "
      f"{fmt(q.get('phrases_grounded'), 2)} of quoted phrases were found verbatim on the page (grounding check).")
    w("- **Two readings of every score:** in-browse ratings cluster on the polite middle for some dimensions (a known effect of rating at the end of a long browsing session); "
      "the scored-after-the-visit reading has the same persona re-rate from its own notes. Where both agree, the result is robust; where they differ, §1 shows both.")
    if ph:
        w("\n" + md_table(["Score", "in-browse mean (sd)", "scored mean (sd)", "η² visitor kind (in / scored)", "η² visit intent (in / scored)"],
                          [[DIM_TITLES[k], f"{fmt(v.get('mean_in_browse'))} ({fmt(v.get('sd_in_browse'))})", f"{fmt(v.get('mean_scored'))} ({fmt(v.get('sd_scored'))})",
                            f"{fmt(v['eta2']['audience_group']['in_browse'])} / {fmt(v['eta2']['audience_group']['scored'])}",
                            f"{fmt(v['eta2']['visit_intent']['in_browse'])} / {fmt(v['eta2']['visit_intent']['scored'])}"] for k, v in ph.items()]))
        w("\n*η² = share of score variance explained by the grouping (0.01 small, 0.06 medium, 0.14 large).*")
    w("- **Limits:** personas are modelled, not recruited; scores are indicators, not measured approval. Trust sits at 3 for nearly everyone in both readings — the anchor "
      "(\"a credible company, but the claims are unproven for my case\") is the honest first-visit answer, so the useful trust signal is *what they would need before going further* "
      "and *which claims they wanted proof for* (§1, §3), not the score.")
    w("")
    return "\n".join(o)


# ----------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("job", type=Path)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--max-chunks", type=int, default=0, help="cap chunks per (text, visitor kind) - for a quick test")
    ap.add_argument("--out", type=Path, default=None, help="default <job>/report")
    a = ap.parse_args()
    job = a.job.resolve()
    out = a.out or (job / "report")
    out.mkdir(parents=True, exist_ok=True)

    rows = load_texts(job)
    if not rows:
        sys.stderr.write("no passed trials with structured output\n")
        return 1
    page = (rows[0]["quality"].get("page_id")) or "homepage"
    # Page sections are written from visitors who read the page; exits are reported for everyone.
    page_rows = [r for r in rows if r["stayed"]] or rows
    pros = [r for r in rows if r["prospect"]] or rows
    sys.stderr.write(f"{len(rows)} passed trials · page {page} · {len(page_rows)} read the page · {len(pros)} prospects\n")

    summary_md, numbers = sr.build(job)
    (out / "ablation_summary.md").write_text(summary_md)
    # extra numbers the report needs
    numbers["missing_info_counts"] = dict(collections.Counter(m for r in rows for m in ((r["quality"].get("missing_info") or []))))
    by_g = collections.defaultdict(list)
    for r in rows:
        by_g[r["audience"]].append(r["quality"].get("scores_post_hoc") or {})
    numbers["scores_by_audience_scored"] = {g: {k: (statistics.mean(v) if (v := [s.get(k) for s in ss if isinstance(s.get(k), (int, float))]) else None) for k in DIMS + EXTRA} for g, ss in by_g.items()}

    facts = page_facts(job)
    hard = {"page_facts": facts, "wording": most_flagged_wording(page_rows), "scores": prospect_scores(pros), "scores_by_audience_scored": numbers["scores_by_audience_scored"],
            "exit_rate": numbers.get("exit_rate"), "exits": exits_by_segment(rows), "next_step": numbers.get("next_step"),
            "trust_action": numbers.get("trust_action"), "missing_info": numbers["missing_info_counts"], "n": len(rows),
            "n_read_page": len(page_rows), "n_prospects": len(pros), "trust": trust_block(pros, rows),
            "scores_by_audience": {g: {k: (statistics.mean(v) if (v := [r["quality"]["scores_in_browse"].get(k) for r in pros if r["audience"] == g and isinstance(r["quality"]["scores_in_browse"].get(k), (int, float))]) else None) for k in DIMS + EXTRA}
                                   for g in {r["audience"] for r in pros}}}
    analytics = (json.loads(sr.ANALYTICS.read_text()).get("pages", {}).get(page, {}) if sr.ANALYTICS.is_file() else {})

    model = Model(a.model, out / "cache")
    reduced = run_map_reduce(model, page_rows, a.chunk, a.workers, a.max_chunks, facts["next_steps"])
    synth = model.json(synth_prompt(PAGE_TITLES.get(page, page), reduced, hard, analytics), 12000, "synth",
                       ("executive_summary", "audience_differences", "journey", "priorities", "retain"))
    synth["trust_advice"] = model.json(trust_prompt(PAGE_TITLES.get(page, page), hard["trust"], hard["wording"], reduced.get("findings") or {}), 8000, "trust",
                                       ("where_trust_stops", "what_would_move_the_next_rung", "claims", "advice"))
    sys.stderr.write(f"synthesis done · model calls {model.calls} (cached {model.cached}) · tokens in/out {model.tokens}\n")

    md = build_markdown(page, job, rows, numbers, reduced, hard, synth, analytics, a.model)
    (out / "partner_report.md").write_text(md)
    (out / "partner_report.json").write_text(json.dumps({"page": page, "job": job.name, "n": len(rows), "numbers": numbers, "hard": hard,
                                                          "reduced": reduced, "synthesis": synth, "model": a.model,
                                                          "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}, ensure_ascii=False, indent=1, default=str))
    sys.stderr.write(f"wrote {out / 'partner_report.md'} ({len(md)} chars)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
