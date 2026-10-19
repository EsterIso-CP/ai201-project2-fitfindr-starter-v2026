"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tokens(text: str) -> set[str]:
    """Lowercase word tokens, with a trailing plural 's' stripped so that
    'tees' matches 'tee' and 'jeans' matches 'jean' on both sides."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words}


def _size_matches(requested: str, listing_size: str | None) -> bool:
    """Whole-token size match, case-insensitive.

    The listing size is split on '/' into tokens, and the request must equal
    one whole token (or the whole size string). So 'M' matches 'M' and 'S/M',
    but 'S' does not match 'XS', 'US 9' or 'XL'.
    """
    if not listing_size:
        return False
    want = requested.strip().lower()
    have = listing_size.strip().lower()
    if want == have:
        return True
    return want in [part.strip() for part in have.split("/")]


def _listing_text(listing: dict) -> str:
    """Everything searchable about a listing. brand is often None."""
    parts = [
        listing.get("title"),
        listing.get("description"),
        listing.get("category"),
        listing.get("brand"),
        " ".join(listing.get("style_tags") or []),
        " ".join(listing.get("colors") or []),
    ]
    return " ".join(p for p in parts if p)


def _describe_wardrobe_item(item) -> str:
    """One line per wardrobe item, tolerant of whatever shape the items have."""
    if isinstance(item, dict):
        name = item.get("name") or item.get("title") or item.get("item")
        details = [
            str(v)
            for k, v in item.items()
            if v and k not in ("name", "title", "item", "id")
        ]
        base = str(name) if name else ""
        extra = ", ".join(details)
        return f"{base} ({extra})" if base and extra else (base or extra or str(item))
    return str(item)


def _describe_listing(item: dict) -> str:
    brand = item.get("brand")
    brand_part = f" by {brand}" if brand else ""
    colors = ", ".join(item.get("colors") or [])
    tags = ", ".join(item.get("style_tags") or [])
    return (
        f"{item.get('title', 'an item')}{brand_part} "
        f"(category: {item.get('category', 'n/a')}; colors: {colors or 'n/a'}; "
        f"style: {tags or 'n/a'}; size: {item.get('size', 'n/a')}; "
        f"condition: {item.get('condition', 'n/a')})"
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Returns a list of at most config.SEARCH_RESULT_LIMIT listing dicts, best
    match first. Every returned listing has a keyword score above zero. Ties are
    broken by lower price, then by id. Returns [] when nothing matches — never
    None, never an exception.

    Score = number of distinct description words (lowercased, plural 's'
    stripped) found in the listing's title, description, category, brand,
    style_tags and colors.
    """
    query = _tokens(description)
    if not query:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing.get("size")):
            continue

        title_words = _tokens(listing.get("title"))
        all_words = _tokens(_listing_text(listing))
        score = sum(2 if w in title_words else 1 for w in query if w in all_words)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"], str(pair[1]["id"])))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    With a non-empty wardrobe the suggestions name pieces the user already
    owns. With an empty (or missing) wardrobe it returns general styling
    advice. Always returns a non-empty string.
    """
    item_line = _describe_listing(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            "You are a friendly thrift-fashion stylist. Someone is thinking "
            f"about buying this secondhand piece: {item_line}.\n\n"
            "They haven't told you what's in their wardrobe, so give one or "
            "two general outfit ideas for this piece, using common basics "
            "most people own. Keep it under 120 words, casual and specific."
        )
    else:
        wardrobe_lines = "\n".join(f"- {_describe_wardrobe_item(i)}" for i in items)
        prompt = (
            "You are a friendly thrift-fashion stylist. Someone is thinking "
            f"about buying this secondhand piece: {item_line}.\n\n"
            f"Here is what they already own:\n{wardrobe_lines}\n\n"
            "Suggest one or two outfits that combine the new piece with items "
            "from their wardrobe. Name the specific wardrobe pieces you're "
            "using. Keep it under 120 words, casual and specific."
        )

    response = (generate(prompt) or "").strip()
    if not response:
        return (
            f"Couldn't generate outfit ideas for {new_item.get('title', 'this item')} "
            "right now. Try again."
        )
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    Returns a two-to-four sentence caption. If `outfit` is empty or
    whitespace-only, returns a descriptive message without calling the model.
    """
    if not outfit or not outfit.strip():
        return "No outfit to write a caption for — run suggest_outfit first."

    title = new_item.get("title", "this piece")
    price = new_item.get("price")
    price_text = f"${price:.2f}" if isinstance(price, (int, float)) else "a steal"
    platform = new_item.get("platform", "a thrift app")

    prompt = (
        "Write a social media caption (2 to 4 sentences) about a thrift find, "
        "the way a real person would post it, not like a product listing.\n\n"
        f"The find: {title}\n"
        f"Price: {price_text}\n"
        f"Platform: {platform}\n"
        f"How it's styled: {outfit.strip()}\n\n"
        "Rules: mention the item, the price, and the platform exactly once "
        "each in the whole caption, and hashtags count as mentions, so never "
        "put the platform name inside a hashtag (no #depopfinds, #poshmarkstyle "
        "and the like). Be specific about the vibe. No hashtags spam (at most "
        "two). Return only the caption."
    )

    response = (generate(prompt) or "").strip()
    if not response:
        return f"Couldn't write a caption for {title} right now. Try again."
    return response