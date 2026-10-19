#!/usr/bin/env python3
"""
Score a run from run_eval.py against the five criteria in criteria.md.

    python score_run.py                          scores the newest results/*.json
    python score_run.py results/run_..._before.json

run_eval.py deliberately leaves PASS/FAIL blank. This is where those judgments
live, written as string tests so the same rules score "before" and "after".
Each check below quotes the criterion it comes from. It prints the run-log
table plus the reason for every FAIL, and writes both next to the run as
*_scored.md.

The size check is written out again here rather than imported from tools.py,
so the code under test isn't grading itself.
"""

import json
import re
import sys
from pathlib import Path

import config

HINTS = ("drop the size", "raise the price", "keywords")


# ── helpers ──────────────────────────────────────────────────────────────────

def _trace_ids(trace: str, step: str) -> list[str]:
    """Listing ids that went into `step`, read from its 'in:' line."""
    return re.findall(rf"\] {step}\n\s+in:\s+new_item=(\S+)", trace)


def _price_count(text: str, price: float) -> int:
    """How many times the price appears, as $52 or $52.00 (not $520)."""
    forms = "|".join(re.escape(f) for f in (f"{price:.2f}", f"{price:g}"))
    return len(re.findall(rf"\$(?:{forms})(?!\d)(?!\.\d)", text))


def _mention_count(text: str, word: str) -> int:
    """Case-insensitive, anywhere — hashtags included. '#depopfinds' names the
    platform as plainly as 'on Depop' does, so it counts."""
    return len(re.findall(re.escape(word), text, re.I))


def _sentences(text: str) -> list[str]:
    """Sentences, with hashtags removed first so a trailing tag line isn't one."""
    text = re.sub(r"#\w+", "", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if re.search(r"[A-Za-z]", p)]


def _size_ok(requested: str, listing_size: str | None) -> bool:
    """The whole-token rule from the Tool Inventory, written independently."""
    if not listing_size:
        return False
    want = requested.strip().lower()
    tokens = [t.strip() for t in listing_size.lower().split("/")]
    return want == listing_size.strip().lower() or want in tokens


def _completed(t: dict) -> bool:
    s = t.get("session") or {}
    return not t.get("crashed") and not s.get("error") and bool(s.get("fit_card"))


# ── one check per criterion; each returns (passed, reason) ───────────────────

def check_1(t):
    """Completes all three tool calls and returns a fit card."""
    if t.get("crashed"):
        return False, f"crashed: {t['crashed']}"
    s = t["session"]
    if s.get("error"):
        return False, f"stopped early: {s['error']}"
    for step in ("search_listings", "suggest_outfit", "create_fit_card"):
        if f"] {step}" not in t["trace"]:
            return False, f"{step} missing from the trace"
    if not (s.get("fit_card") or "").strip():
        return False, "no fit card"
    return True, ""


# Revised criterion 1 (unit 4): for each phrasing, the listings a person would
# accept as a match, read off the data by hand.
ACCEPTABLE = {
    "vintage graphic tee under $30": {"lst_002", "lst_006", "lst_033"},
    "retro band shirt": {"lst_006", "lst_033"},
    "cozy hoodie under $40": {"lst_015"},
    "chunky white sneakers": {"lst_019"},
    "y2k top size S": {"lst_002", "lst_017"},
}


def check_1_revised(t):
    """Completes all three tools AND the selected item is an acceptable match."""
    ok, why = check_1(t)
    if not ok:
        return ok, why
    picked = t["session"]["selected_item"]
    wanted = ACCEPTABLE.get(t["query"])
    if wanted is None:
        return False, f"no acceptable set written for {t['query']!r}"
    if picked["id"] not in wanted:
        return False, f"picked {picked['id']} {picked['title']}, wanted one of {sorted(wanted)}"
    return True, ""


def check_2(t):
    """Stops before suggest_outfit, with a message naming what to change."""
    if t.get("crashed"):
        return False, f"crashed: {t['crashed']}"
    s = t["session"]
    if not s.get("error"):
        return False, "didn't stop"
    if "] suggest_outfit" in t["trace"] or s.get("outfit_suggestion") is not None:
        return False, "suggest_outfit was called"
    if not any(h in s["error"].lower() for h in HINTS):
        return False, f"message names nothing to change: {s['error']}"
    return True, ""


def check_3(t):
    """search[0].id == selected_item.id == what suggest_outfit and
    create_fit_card received; fit card price == selected_item price."""
    if not _completed(t):
        return False, "didn't complete, so there's no handoff to compare"
    s = t["session"]
    ids = {
        "search_listings[0]": s["search_results"][0]["id"],
        "selected_item": s["selected_item"]["id"],
        "suggest_outfit got": (_trace_ids(t["trace"], "suggest_outfit") or ["?"])[0],
        "create_fit_card got": (_trace_ids(t["trace"], "create_fit_card") or ["?"])[0],
    }
    if len(set(ids.values())) != 1:
        return False, f"ids differ: {ids}"
    price = s["selected_item"]["price"]
    if _price_count(s["fit_card"], price) < 1:
        return False, f"fit card doesn't show selected_item's price ${price:g}"
    return True, ""


def check_4(t):
    """(a) 2-4 sentences, price exactly once, platform exactly once.
    Part (b), no two identical, is checked across tries in score()."""
    if not _completed(t):
        return False, "no fit card"
    s = t["session"]
    card, item = s["fit_card"], s["selected_item"]
    problems = []
    n = len(_sentences(card))
    if not 2 <= n <= 4:
        problems.append(f"{n} sentences")
    p = _price_count(card, item["price"])
    if p != 1:
        problems.append(f"price ${item['price']:g} appears {p}×")
    w = _mention_count(card, item["platform"])
    if w != 1:
        problems.append(f"platform '{item['platform']}' appears {w}×")
    return (not problems), "; ".join(problems)


def check_5(t):
    """Zero returned listings over max_price or outside the size."""
    if t.get("crashed"):
        return False, f"crashed: {t['crashed']}"
    s = t["session"]
    size, max_price = s["parsed"].get("size"), s["parsed"].get("max_price")
    if size is None or max_price is None:
        return False, f"query didn't parse to both a size and a price: {s['parsed']}"
    bad = [
        f"{l['id']} (size {l['size']}, ${l['price']:g})"
        for l in s.get("search_results") or []
        if l["price"] > max_price or not _size_ok(size, l["size"])
    ]
    if bad:
        return False, "violations: " + ", ".join(bad)
    return True, ""


CHECKS = {1: check_1, 2: check_2, 3: check_3, 4: check_4, 5: check_5}
TARGETS = {1: 4, 2: 5, 3: 5, 4: 4, 5: 5}


# ── scoring ──────────────────────────────────────────────────────────────────

def score(path: Path) -> str:
    rows = json.loads(path.read_text(encoding="utf-8"))
    table = [
        "| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    notes = []

    for row in rows:
        sc = row["scenario"]
        n = sc.get("criterion")
        if n not in CHECKS:
            continue
        results = [CHECKS[n](t) for t in row["tries"]]
        cells = ["PASS" if ok else "FAIL" for ok, _ in results]
        passes = cells.count("PASS")
        met = passes >= TARGETS[n]

        if n == 4:
            cards = [(t.get("session") or {}).get("fit_card") for t in row["tries"]]
            cards = [c for c in cards if c]
            dupes = len(cards) - len(set(cards))
            if dupes:
                met = False
                notes.append(f"- 4(b): {dupes} fit card(s) word-for-word identical to another")
            else:
                notes.append(f"- 4(b): all {len(cards)} fit cards differ — no identical pair")

        verdict = f"{'MET' if met else 'MISSED'} ({passes}/{len(cells)})"
        table.append(
            f"| {n}. {sc['name']} | {TARGETS[n]} of 5 | {' | '.join(cells)} | {verdict} |"
        )
        for i, (ok, why) in enumerate(results, 1):
            if not ok:
                notes.append(f"- {n}, try {i} (`{row['tries'][i - 1]['query']}`): {why}")

        if n == 1:
            revised = [check_1_revised(t) for t in row["tries"]]
            cells = ["PASS" if ok else "FAIL" for ok, _ in revised]
            passes = cells.count("PASS")
            verdict = f"{'MET' if passes >= TARGETS[1] else 'MISSED'} ({passes}/{len(cells)})"
            table.append(
                f"| 1 (revised). … and picks an acceptable match | {TARGETS[1]} of 5 "
                f"| {' | '.join(cells)} | {verdict} |"
            )
            for i, (ok, why) in enumerate(revised, 1):
                if not ok:
                    notes.append(f"- 1 (revised), try {i} (`{row['tries'][i - 1]['query']}`): {why}")

    out = "\n".join(table)
    if notes:
        out += "\n\n**Why each FAIL failed, and other checks:**\n\n" + "\n".join(notes)
    return out + "\n"


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        runs = sorted(config.RESULTS_DIR.glob("run_*.json"))
        if not runs:
            sys.exit("No results/run_*.json yet. Run `python run_eval.py --label before` first.")
        path = runs[-1]

    text = f"# Scored: {path.name}\n\nProduced by `score_run.py::score`.\n\n" + score(path)
    out = path.with_name(path.stem + "_scored.md")
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"Wrote {out.relative_to(config.ROOT) if out.is_relative_to(config.ROOT) else out}")


if __name__ == "__main__":
    main()
