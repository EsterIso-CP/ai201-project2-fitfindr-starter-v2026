"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # Criterion 1 says five different phrasings, not one query five times,
        # so each try gets its own query. All five match at least one listing.
        "name": "matching query completes",
        "queries": [
            "vintage graphic tee under $30",
            "retro band shirt",
            "cozy hoodie under $40",
            "chunky white sneakers",
            "y2k top size S",
        ],
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # Criterion 2 — the branch. Five impossible queries, each blocked by a
        # different thing: keywords, price, size, size, price. The message
        # should point at the one that's blocking.
        "name": "impossible query stops early",
        "queries": [
            "designer ballgown size XXS under $5",
            "bomber jacket under $20",
            "velvet blazer size XL",
            "chelsea boots size S",
            "silk slip dress under $10",
        ],
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3 — state. Any matching query works; what's checked is the
        # listing id at each handoff, read from the session and the trace.
        "name": "selected item is the one passed on",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 — the fit card. The same query every try, so the same item
        # (Velvet Blazer, $52, depop) goes into create_fit_card five times.
        "name": "fit card is a caption and varies",
        "query": "velvet blazer",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5 — filters. Five queries, each with a size and a max_price.
        # Each size has a near miss in the data: S vs S/M, L vs XL and L/XL,
        # M vs M/L, W28 vs W27/W29.
        "name": "filters are respected",
        "queries": [
            "tee size S under $20",
            "vintage top size L under $25",
            "jacket size M under $40",
            "blazer size S under $60",
            "jeans size W28 under $35",
        ],
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def query_for(scenario: dict, attempt: int) -> str:
    """The query for one try. A scenario has either one "query" used on every
    try, or a "queries" list with one per try (try 1 gets the first)."""
    if scenario.get("queries"):
        queries = scenario["queries"]
        return queries[(attempt - 1) % len(queries)]
    return scenario["query"]


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        queries = scenario.get("queries") or [scenario.get("query", "")]
        if not all(q.strip() for q in queries):
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
