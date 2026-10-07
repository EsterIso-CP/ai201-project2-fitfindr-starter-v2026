"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config  # noqa: F401
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable  # noqa: F401 — handled in unit 4


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """A fresh session for one user interaction. Single source of truth for a run."""
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one chosen — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing (regex) ─────────────────────────────────────────────────────

_PRICE_RE = re.compile(
    r"(?:under|below|less than|up to|at most|max(?:imum)?|<=?)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_BARE_PRICE_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
_SIZE_RE = re.compile(
    r"\bsize\s*:?\s*([A-Za-z0-9]+(?:/[A-Za-z0-9]+)?)", re.IGNORECASE
)
_FILLER_RE = re.compile(
    r"\b(?:i'?m|i am|i want|i need|looking for|look for|find me|find|show me|"
    r"search for|please|a|an|the|some|in|for|under|below|size)\b",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """Pull description, size and max_price out of a plain-language query.

    Regex and string cleanup, no model call: "vintage graphic tee under $30,
    size M" -> {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}.
    size and max_price are None when the query doesn't give one.
    """
    text = query or ""

    max_price = None
    price_match = _PRICE_RE.search(text) or _BARE_PRICE_RE.search(text)
    if price_match:
        max_price = float(price_match.group(1))
        text = text.replace(price_match.group(0), " ")

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1)
        text = text.replace(size_match.group(0), " ")

    text = _FILLER_RE.sub(" ", text)
    text = re.sub(r"[^\w\s'-]", " ", text)
    description = " ".join(text.split())

    return {"description": description, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """Say what the user could change. Re-runs the search with one filter
    dropped at a time to find out which filter is the blocker."""
    description = parsed["description"]
    size, max_price = parsed["size"], parsed["max_price"]

    applied = []
    if size:
        applied.append(f"size {size}")
    if max_price is not None:
        applied.append(f"under ${max_price:g}")
    applied_text = f" in {' and '.join(applied)}" if applied else ""
    base = f"Nothing matched '{description}'{applied_text}."

    hints = []
    if size:
        without_size = search_listings(description, None, max_price)
        if without_size:
            hints.append(
                f"{len(without_size)} listing(s) match if you drop the size "
                f"filter (try a different size than {size})"
            )
    if max_price is not None:
        without_price = search_listings(description, size, None)
        if without_price:
            cheapest = min(l["price"] for l in without_price)
            hints.append(
                f"{len(without_price)} listing(s) match if you raise the price "
                f"limit (the cheapest is ${cheapest:g})"
            )
    if not hints:
        hints.append("try different or fewer keywords, like 'tee' instead of 'vintage graphic tee'")

    return base + " " + "; ".join(hints).capitalize() + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def _next_step(session: dict) -> str:
    """Decide the next step by looking at what the session already holds."""
    if not session["parsed"]:
        return "parse"
    if session["selected_item"] is None:
        return "search"
    if session["outfit_suggestion"] is None:
        return "outfit"
    if session["fit_card"] is None:
        return "card"
    return "done"


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    **Check session["error"] first** — if it isn't None, the run ended early
    and the later fields will still be None.

    Branch rule: if search_listings returns an empty list, put a message
    naming what to change in session["error"] and return. Otherwise select the
    first result and continue to suggest_outfit, then create_fit_card. If
    suggest_outfit returns an empty string, record an error and stop instead of
    calling create_fit_card.
    """
    session = new_session(query, wardrobe)

    count = 0
    while session["error"] is None:
        count += 1
        trace.check_iterations(count)

        step = _next_step(session)

        if step == "parse":
            parsed = parse_query(session["query"])
            session["parsed"] = parsed
            if not parsed["description"]:
                session["error"] = (
                    "I couldn't find any item words in that. Describe what you "
                    "want, e.g. 'vintage graphic tee under $30, size M'."
                )

        elif step == "search":
            p = session["parsed"]
            results = search_listings(p["description"], p["size"], p["max_price"])
            session["search_results"] = results
            if not results:  # THE BRANCH: nothing found, so stop here
                session["error"] = _no_results_message(p)
            else:
                session["selected_item"] = session["search_results"][0]

        elif step == "outfit":
            outfit = suggest_outfit(session["selected_item"], session["wardrobe"])
            if not outfit or not outfit.strip():
                session["error"] = "Couldn't come up with an outfit for that item. Try again."
            else:
                session["outfit_suggestion"] = outfit

        elif step == "card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )

        else:  # "done"
            break

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )