# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---


<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is a small thrift-shopping agent. You describe what you want in plain
language ("vintage graphic tee under $30"), and it searches a set of secondhand
listings, picks the best match, suggests outfits that combine it with pieces
from your wardrobe, and writes a short caption you could post about the find.
It's built from three tools (`search_listings`, `suggest_outfit`,
`create_fit_card`) and a loop that decides what to run next based on what the
last tool returned.

---

## Tool Inventory

### `search_listings`

- **What it does:** Finds thrift listings whose text matches the keywords in a description, optionally filtered by size and a price ceiling, and ranks them by keyword overlap. It does not call the model.
- **Inputs:** `description` (str, keywords like "vintage graphic tee"); `size` (str | None, None skips size filtering; matched case-insensitively against whole `/`-separated tokens of the listing's size, so "M" matches "M" and "S/M" but not "XL", "XS" or "US 9"); `max_price` (float | None, inclusive ceiling, None skips price filtering).
- **Returns:** A list of at most `config.SEARCH_RESULT_LIMIT` listing dicts, best match first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Every item in the list has a keyword score above zero.
- **When it has nothing:** An empty list `[]`. Never None, never an exception.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfit ideas built around the thrifted item, using the user's wardrobe when they have one.
- **Inputs:** `new_item` (dict, a listing dict as returned by `search_listings`); `wardrobe` (dict with an `items` key holding a list of item dicts, which may be empty).
- **Returns:** A non-empty str with one or two outfit suggestions that name specific pieces from the wardrobe.
- **When it has nothing:** With an empty wardrobe, a non-empty str of general styling advice for the item. Never "" and never an exception.

### `create_fit_card`

- **What it does:** Asks the model to write a short, social-post-style caption about the find, based on the item and the outfit suggestion.
- **Inputs:** `outfit` (str, the output of `suggest_outfit`); `new_item` (dict, a listing dict).
- **Returns:** A str of two to four sentences that mentions the item, its price, and its platform once each, and that varies from run to run.
- **When it has nothing:** If `outfit` is empty or whitespace-only, a descriptive message str (e.g. "No outfit to write a caption for.") returned without calling the model. Never raises.

### Loop branch

If `search_listings` returns an empty list, put a "no matches" message in the session and stop. Otherwise take the first result and call `suggest_outfit`, then pass its string to `create_fit_card`. If `suggest_outfit` returns an empty or whitespace-only string, record an error in the session and stop instead of calling `create_fit_card`.
---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` that names the size, price, and keywords that were applied
and says which one to change, then return the session without calling
`suggest_outfit`. Otherwise take the first result, store it in
`session["selected_item"]`, and go to `suggest_outfit`, then `create_fit_card`.
If `suggest_outfit` returns an empty string, record an error and stop before
`create_fit_card`.

**Where it lives:** `agent.py::run_agent`. The query is parsed with regex
(`agent.py::parse_query`), not by the model.

---

## Sample Run


**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$  python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"  
[{'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Hey friend! Those Vintage Levi's 501s are an absolute holy grail, and since you already own the **white ribbed tank top**, you’ve got the ultimate effortless combo right there. 

**Look 1: Casual Streetwear**
Tuck that white ribbed tank into the 501s, add your **brown leather belt**, and throw on the **black cropped zip hoodie** over top. Finish it with the **chunky white sneakers** and your **black crossbody bag** for a 90s off-duty model vibe. 

**Look 2: Edgy Classic**
Keep the white ribbed tank tucked in with the brown leather belt, but layer your **vintage black denim jacket** over it. Lace up your **black combat boots** for a tougher, timeless look. 

You definitely need these!
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Still in disbelief I scored these vintage Levi's 501 jeans for just $38.00 on depop. Tossed them on with my beat-up white sneakers for the ultimate lazy-Sunday-errands look. Honestly never taking these off. #thriftfind #vintagelevis
```

---
## How I Used AI

**Moment 1**

- *What I asked for:* I had Claude implement `search_listings` from my spec
  (keyword overlap, whole-token size match, price ceiling) and then I tested it.
- *What came back:* A search where every query word counted the same wherever
  it matched. For "graphic tee" in size M, a mesh top (matched only in its
  description) tied with the Y2K Baby Tee and came out first because it was
  cheaper. A diagnostic command showed both listings matched the same two words.
- *What I changed:* I changed the score so a word found in the title is worth
  2 points and a word found elsewhere is worth 1. After that the Baby Tee
  ranked first. I documented the rule in the Tool Inventory.

**Moment 2**

- *What I asked for:* I asked Claude for a check that the item chosen by the
  search is the same one that reaches `suggest_outfit` (my state criterion).
- *What came back:* A one-line `python -c` command written with bash escaping.
  It failed with a SyntaxError in PowerShell because of the `\$` in the query.
- *What I changed:* I didn't want to add a file, so I asked for another way and
  ran it as a PowerShell here-string instead. It printed `lst_002` for the
  selected item, the item `suggest_outfit` received, and the first search hit,
  with `match: True`.

**Moment 3 (unit 4)**

- *What I asked for:* I had Claude turn my five criteria into scenarios and
  write `score_run.py`, so each PASS/FAIL comes from a string test, as
  criteria.md promises, not from me reading 25 outputs.
- *What came back:* A scorer that gave 5/5 on everything. To decide what
  "contains its platform once" meant, it chose a rule where `#depopfinds` was
  not a mention of Depop. That rule made criterion 4 MET.
- *What I changed:* When I gave Claude the Milestone 4 instructions ("read
  them plainly"), it re-checked its own rule and flagged it as the generous
  reading. I agreed: a hashtag naming the platform is a mention. Re-scored
  that way, criterion 4 is MISSED (0/5): 17 of 25 cards tag the platform. I
  kept the correction visible in the Run Log instead of quietly swapping the
  table. The lesson: the generous reading was hiding inside a helper function
  I hadn't read closely.

**Moment 4 (unit 4)**

- *What I asked for:* Nothing specific. When the before-run came back 25/25,
  Claude checked that the scorer could actually fail before reporting it,
  because the result looked too clean to trust.
- *What came back:* It fed the scorer copies of real tries with one thing
  broken in each: an XS listing in an S search, a price over the limit, a
  mismatched id, a `suggest_outfit` step after an empty search, and so on.
  Every one came back FAIL with the right reason.
- *What I changed:* Nothing in the scorer. It also flagged that criterion 4
  says "same item **and outfit**", while `run_agent` writes a new outfit each
  try, so it added a direct `create_fit_card` run with the outfit held fixed.
  I kept that run as evidence, because it measures the criterion as I
  actually wrote it.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 1 (revised in unit 4). … and the selected item is an acceptable match | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the one the next tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a caption and varies between runs | 4 of 5, no repeats | FAIL | FAIL | FAIL | FAIL | FAIL | MISSED (0/5; 5 distinct) |
| 5. Filters are respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

How this was run and scored:

- **Run:** `python run_eval.py --label before`, cache off, temperature 0.9.
  Raw output is in `results/run_2026-10-19_1130_before.md` and `.json`.
- **Scenarios** (`scenarios.py`): criteria 1, 2 and 5 use a different query
  on each try, because the criteria ask for five phrasings or five queries.
  - Criterion 2's five queries are each blocked by something different:
    keywords, price, size, size, price.
  - Criterion 5's queries each have a near-miss size in the data: S vs S/M,
    L vs XL and L/XL, M vs M/L, W28 vs W27/W29.
  - Criteria 3 and 4 repeat one query five times.
- **Scored** by `python score_run.py`. Every check is a string test written
  out in `score_run.py::check_1` … `check_5`. Scored table:
  `results/run_2026-10-19_1130_before_scored.md`.
- **Checking the scorer:** I fed it copies of real tries with one thing
  broken: an XS listing in an S search, a price over the limit, the price and
  platform said twice, a mismatched id, a `suggest_outfit` step after an
  empty search, and an empty fit card. It marked every one FAIL.
- **Rules I had to choose for criterion 4:**
  - Hashtags are removed before counting sentences.
  - A platform mention counts anywhere, hashtags included, so `#depopfinds`
    is a mention.
  - Price matches `$52` or `$52.00`.
- **Correction:** I first scored criterion 4 with platform hashtags not
  counted, and it came out MET (5/5). That was the generous reading.
  "Contains its platform once" plainly includes `#depopstyle`. Re-scored the
  plain way, it's MISSED (0/5). This table is the corrected one, from the
  same run with no re-run.
- **Criterion 4 says "same item and outfit."** Through `run_agent`,
  `suggest_outfit` writes a new outfit on each try, which makes "no repeats"
  easier to pass. So I also called `create_fit_card` five times directly,
  with try 1's item and outfit held fixed. With the plain rule that scored
  2/5 for (a) and 5 distinct for (b), so it's a miss either way. Output is in
  `results/run_2026-10-19_1130_before_fitcard_fixed.txt`.

**Real output from one try per criterion**

Every trace below is from `agent.py::run_agent` (the `trace.step()` calls).
The fit card comes from `tools.py::create_fit_card` and the error messages
from `agent.py::_no_results_message`.

Criterion 1, try 2 (`retro band shirt`). This one completed, but it picked a
polo over the band tee:

```
[2] search_listings (via MCP)
      in:  {'description': 'retro band shirt', 'size': None, 'max_price': None}
      out: 5 items: Vintage Polo Shirt — Forest Green, Vintage Band Tee — Faded Grey, Oversized Flannel Shirt — Plaid Red/Black … +2 more
      →    branch: selected lst_024 Vintage Polo Shirt — Forest Green
[3] suggest_outfit
      in:  new_item=lst_024 'Vintage Polo Shirt — Forest Green', wardrobe=10 items
      out: Hey friend! You *definitely* need to grab that forest green polo—it's such a timeless staple.   Here are two w…
[4] create_fit_card
      in:  new_item=lst_024 'Vintage Polo Shirt — Forest Green', outfit=726 chars from step above
fit_card: Scored this forest green vintage polo on thredUp for just $18.00 and I’m obsessed. It gives the ultimate preppy-meets-grunge vibe whether I dress it down with baggy denim or lean into the retro campus look. #thriftfind #styletips
```

Criterion 2, try 2 (`bomber jacket under $20`):

```
[2] search_listings (via MCP)
      in:  {'description': 'bomber jacket', 'size': None, 'max_price': 20.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
error: Nothing matched 'bomber jacket' in under $20. 4 listing(s) match if you raise the price limit (the cheapest is $33).
```

Criterion 3, try 1 (`denim jacket under $50`). It's lst_007 at every handoff,
and the fit card says $42, which is the listing's price:

```
      →    branch: selected lst_007 Denim Jacket — Light Wash, Cropped
[3] suggest_outfit
      in:  new_item=lst_007 'Denim Jacket — Light Wash, Cropped', wardrobe=10 items
[4] create_fit_card
      in:  new_item=lst_007 'Denim Jacket — Light Wash, Cropped', outfit=760 chars from step above
fit_card: Obsessed is an understatement for this cropped light-wash denim jacket I just scored on Poshmark for $42. It has the absolute best 90s streetwear vibe and literally goes with every baggy pant I own. Can't wait to live in this all fall! #thriftfind #poshmarkstyle
```

Criterion 4, try 1 (`velvet blazer`, lst_036, $52, depop). FAIL: it has 3
sentences and $52 once, but the platform twice ("on Depop" and `#depop`):

```
Still not over finding this emerald green velvet blazer on Depop for $52! It gives off the ultimate effortless vintage glam vibe when thrown over basic trousers, but looks equally good dressed down with baggy denim. Grab it before I change my mind and keep it! #thriftfinds #depop
```

Criterion 5, try 2 (`vintage top size L under $25`). Every result is size L or
L/XL and at most $25:

```
[2] search_listings (via MCP)
      in:  {'description': 'vintage top', 'size': 'L', 'max_price': 25.0}
      out: 3 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Tie-Dye Long Sleeve — Pastel
search_results: lst_033 (L, $19), lst_006 (L, $24), lst_040 (L/XL, $17)
```

**Also seen, not a miss:** Criterion 2's messages always name the right thing
to change, but the wording is rough. It says "in under $20", and it lowercases
the size ("a different size than xl"), because `.capitalize()` in
`agent.py::_no_results_message` lowercases everything after the first letter.

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | **MET (5/5)** | All five phrasings ran search → outfit → fit card and returned a card. Read plainly it's met, but it only checks completion (see the revision below). |
| 1r | *Revised:* … and the selected item is an acceptable match | 4 of 5 | **MET (4/5)** | Four picks were in the hand-written acceptable set. `retro band shirt` picked a polo shirt, which isn't. 4 passes against a target of 4 is met, with no room to spare. |
| 2 | An impossible query stops before the second tool | 5 of 5 | **MET (5/5)** | All five stopped after `search_listings`, with no `suggest_outfit` in the trace. Each message named the blocker (keywords, raise the price, or drop the size), and it was the right one each time. |
| 3 | The selected item is the one the next tool receives | 5 of 5 | **MET (5/5)** | lst_007 was the id at all four handoffs in every try: `search_listings[0]`, `selected_item`, `suggest_outfit`'s input and `create_fit_card`'s input. Every card said $42. |
| 4 | The fit card is a caption and varies between runs | 4 of 5, no repeats | **MISSED (0/5)** | (b) held, with five distinct cards. (a) failed on every try: each card named Depop twice, once in the caption and once in a hashtag. Holding the outfit fixed also gave a miss, at 2/5. |
| 5 | Filters are respected | 5 of 5 | **MET (5/5)** | 0 violations across 8 returned listings from 5 queries. Every price was at most the limit, and every size was a whole-token match (S → S/M, L → L and L/XL, M → M/L, W28 → W28). |

**Diagnoses**

**Criterion 4 missed: one problem, in the model's output, caused by the
prompt.** Every failure is the same thing. The caption names the platform once
in its sentences, then again inside a hashtag (`#depop`, `#depopfinds`,
`#depopstyle`). Across all 25 fit cards in the run (every scenario, not just
criterion 4's), the sentences named the platform exactly once in 25 of 25. A
platform hashtag added a second mention in 17 of 25. Every card had exactly
one price and 2–4 sentences, so length and price never failed. The prompt in
`tools.py::create_fit_card` gives the model `Platform: depop` as a labelled
field. It then says "mention the item, the price, and the platform exactly
once each" and, in a separate sentence, "No hashtags spam (at most two)". The
model treats hashtags as separate from the caption: it keeps the "once" rule
in the sentences, then builds the hashtags from the platform name, which is
how resale posts are usually tagged. The tool runs and the rules it states are
followed. The prompt never says a hashtag counts as a mention, so nothing
stops it. The variation also points away from chance. It happened on 5 of 5
velvet-blazer cards, which shows it isn't one item's quirk. Holding the outfit
fixed brought it down to 3 of 5, so it doesn't depend on the outfit text.

**Criterion 1 (revised) met, but its one failed try is deterministic, in a
tool.** `retro band shirt` → Vintage Polo Shirt is `search_listings`, not
the model. "retro" appears nowhere in the data. "shirt" is in the titles of
the polo and the flannel, and "band" is in the band tee's title. A title word
scores 2, so three listings tie at 2. The tie-break is lower price, so the $18
polo beats the $19 band tee. The data calls band tees "tee", never "shirt",
so the user's word for the item type pulls toward the wrong item. Because
there's no randomness, this phrasing fails every time it's asked. It's 1 of 5
only because it's 1 of the 5 phrasings.

**Were my targets too low?** Partly, yes.

- **Criteria 2, 3 and 5** test plain Python with no model in the path, so
  5 of 5 was the only honest target and meeting it was likely. They confirm
  there are no bugs, but they can't show variance.
- **Criterion 1, as written,** could hardly miss: it checked that the run
  finished, not that it found the right thing. That's why I revised it
  instead of just reporting MET.
- **Criterion 4** was the only one aimed at model behaviour, and it's the one
  that missed.
- **The one I'd tighten next is 4(b).** "No two word-for-word identical"
  passed even though 4 of 5 velvet-blazer cards open with "Still …" ("Still
  not over", "Still kicking myself", "Still screaming"). So do 11 of all 25
  cards in the run. A version like "no two of five cards share their first
  three words" would catch that template.



---

## Loop Trace

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style, Y2K Baby Tee — Butterfly Print … +7 more
      →    branch: selected Vintage Band Tee — Faded Grey
[3] suggest_outfit
      in:  new_item='Vintage Band Tee — Faded Grey', wardrobe=10 items
      out: Total yes to this vintage band tee! It’s got that perfect lived-in grunge energy.   Here are two ways to style…
[4] create_fit_card
      in:  new_item='Vintage Band Tee — Faded Grey', outfit=758 chars from step above
      out: Scored this faded grey vintage band tee on depop for just $19 and I am obsessed with the grunge energy. It’s a…
```

**Empty search**

```
$ python app.py ask 'sequined astronaut ballgown size XXS under $3' --trace
[1] parse_query
      in:  sequined astronaut ballgown size XXS under $3
      out: {'description': 'sequined astronaut ballgown', 'size': 'XXS', 'max_price': 3.0}
[2] search_listings (via MCP)
      in:  {'description': 'sequined astronaut ballgown', 'size': 'XXS', 'max_price': 3.0}
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  Nothing matched 'sequined astronaut ballgown' in size XXS and under $3. Try different or fewer keywords, like 'tee' instead of 'vintage graphic tee'.
```

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with a
written description and typed inputs (`description: str`, `size: str | None`,
`max_price: float | None`, matching the Tool Inventory). In
`agent.py::run_agent`, the direct `search_listings(...)` call became
`call_tool("search_listings", {...})`. Nothing behaved differently afterwards.
I ran the same three inputs (a normal search, one with a size filter, and one
with no matches) both ways, and the results were identical lists of dicts
(7, 2 and 0 items). The tool was already returning plain JSON-safe data, so
nothing was lost going through the protocol. `_no_results_message` still calls
`search_listings` directly for its "drop one filter" hints.

### Failure modes, triggered on purpose

**1. Empty search.** `python app.py ask 'sequined astronaut ballgown size XXS under $3'`

```
  Nothing matched 'sequined astronaut ballgown' in size XXS and under $3. Try different or fewer keywords, like 'tee' instead of 'vintage graphic tee'.

0 model calls this session
```

Handled already. The branch stops before `suggest_outfit` and names the
filters that were applied. No handler added.

**2. Empty wardrobe.** `python app.py ask 'vintage graphic tee under $30' --empty-wardrobe`

```
  Found:    Vintage Band Tee — Faded Grey — $19.0 on depop

  Outfit:   Hey babe! Oh, you *have* to grab that vintage band tee—that faded charcoal wash is pure gold and already has that 100% authentic, lived-in softness.
  ...
1. **The Model-Off-Duty:** Tuck it into straight-leg blue jeans, throw on a black leather jacket, and lace up some beat-up Converse or combat boots. ...
2. **The High-Low Mix:** Wear it oversized over a pleated black mini skirt or bike shorts, ...
```

Handled already. `suggest_outfit` switches to a general-advice prompt when
`wardrobe["items"]` is empty, so it returns advice, not an empty string or a
crash. No handler added.

**3. Model unavailable.** One character of the key changed, new query
`python app.py ask 'corduroy jacket for fall under $45'`.

Before (no handler):

```
ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session
```

There was no stack trace, but only because `app.py::main` catches every
exception. `run_agent` itself crashed. The session was lost, the item it had
already found was never shown, and anything else calling `run_agent`
(`run_eval.py`, `serve.py`) would get a raw exception.

Handler added: `run_agent` now catches `ModelUnavailable` around
`suggest_outfit` and `create_fit_card`. It writes a message into
`session["error"]` naming what broke and what to do, then stops. After, with a
new query `python app.py ask 'black leather jacket under $60'`:

```
[3] suggest_outfit
      in:  Platform Mary Janes — Black Patent ($55.0, depop)
      out: ModelUnavailable
      →    model unreachable, stopping

  Found Platform Mary Janes — Black Patent ($55), but couldn't reach the model to write outfit ideas. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Then run the same query again.

1 model calls this session
```



---

## The Improvement

**What I changed:** One prompt, the rules line in `tools.py::create_fit_card`.

Before:

```
"Rules: mention the item, the price, and the platform exactly once each.
 Be specific about the vibe. No hashtags spam (at most two). Return only the caption."
```

After:

```
"Rules: mention the item, the price, and the platform exactly once each in the whole
 caption, and hashtags count as mentions, so never put the platform name inside a
 hashtag (no #depopfinds, #poshmarkstyle and the like). Be specific about the vibe.
 No hashtags spam (at most two). Return only the caption."
```

Nothing else changed. I left the agent, the other tools, the scenarios, the
scorer rules and the temperature alone. I also left the "Still …" openers
alone, even though I'd noticed them, because changing that too would make it
two changes.

**Which failure it was meant to fix:** Criterion 4, MISSED (0/5). Every
failure was the platform named a second time inside a hashtag. The diagnosis
put that in the model's output, caused by a prompt that never said hashtags
count as mentions.

### Run Log — After

`python run_eval.py --label after`, same scenarios, cache off, temperature 0.9.
Raw output: `results/run_2026-10-19_1205_after.md` / `.json`. Scored by
`score_run.py` with the same rules as the before log:
`results/run_2026-10-19_1205_after_scored.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 1 (revised in unit 4). … and the selected item is an acceptable match | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the one the next tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a caption and varies between runs | 4 of 5, no repeats | PASS | PASS | PASS | PASS | PASS | MET (5/5; 5 distinct) |
| 5. Filters are respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 4, try 1, after (`velvet blazer`, lst_036, $52, depop). From
`tools.py::create_fit_card`, via `agent.py::run_agent`. It has 3 sentences,
$52 once, and depop once; the hashtags no longer name the platform:

```
Found this gorgeous emerald green velvet blazer on depop for $52 and honestly, I'm obsessed. It's the ultimate high-low mix when thrown over a basic tank and baggy denim, but looks just as cool layered with a hoodie and combat boots. Going to wear this everywhere this season!

#thriftedstyle #secondhandfashion
```

**Did it help, and how do I know:** Yes, for the failure it targeted.
Criterion 4 went from MISSED (0/5) to MET (5/5). The rows that didn't depend
on the prompt (1, 1-revised, 2, 3 and 5) came out the same as before, which is
what one isolated change should do.

How I know it's the change and not luck: I have two before-runs and one
after-run, each with 25 fit cards (every scenario, not just criterion 4's).

| Run | Platform not exactly once | Platform inside a hashtag | Price not exactly once | Opens with "Still" |
|---|---|---|---|---|
| before, 11:30 (the one scored above) | 17 / 25 | 17 / 25 | 0 / 25 | 11 / 25 |
| before, 11:33 (a second, independent run) | 13 / 25 | 13 / 25 | 1 / 25 | 7 / 25 |
| **after, 12:05** | **0 / 25** | **0 / 25** | **3 / 25** | 5 / 25 |

The two before-runs disagree on criterion 4's own row: 0/5 in one, 2/5 in the
other. So the before rate varies from run to run, but it missed both times.
After the change, the failure that caused every miss (a platform hashtag)
went from 13–17 of 25 cards to 0 of 25. That's a big enough drop that I don't
think it's chance.

**What got worse, possibly.** Three after cards wrote the price in words
("fifteen bucks", "thirty bucks", "forty-two dollars"), so the price check
finds it 0 times. The before-runs had 0 and 1 of these. None were in criterion
4's scenario or criterion 3's (whose price check would have failed), so no
verdict changed. My guess is that the stronger "count every mention" wording
pushes the model to avoid repeating anything that looks like a token,
including the dollar figure. But 3 vs 0–1 out of 25 is small enough that it
could be noise, and I haven't tested it.

---

## What's Still Broken

Every criterion is MET in the after-run. What's left:

- **Wrong item for some phrasings (revised criterion 1, 4/5, met only just).**
  `retro band shirt` styles a polo shirt in every run, because
  `search_listings` breaks a three-way score tie by lowest price, not
  relevance. The data calls band tees "tee", never "shirt", so the user's word
  for the item type pulls toward the wrong listing.
  - *What I'd do:* score a word that only a few listings contain ("band")
    above a word lots of listings contain ("shirt"), so rarer words decide
    ties. Or treat shirt/tee/top as the same item type.
  - *Why I stopped:* the criterion is met, and the milestone asked for one
    change. I spent it on the criterion that actually missed. Changing search
    would also change which item every other scenario picks, so it needs its
    own before/after.
- **Price written in words (3 of 25 after cards).** See above. It didn't miss
  a criterion this run, but if it lands in criterion 3's or 4's scenario, it
  will.
  - *What I'd do:* add "write the price exactly as given, e.g. $52" to the
    prompt. Then run it again to see whether the 3/25 was the change or noise.
- **Near-template captions.** 5 of 25 after cards (7–11 of 25 before) open
  with "Still …". Criterion 4(b) only catches word-for-word repeats, so this
  passes.
  - *What I'd do:* tighten 4(b) to "no two of five cards share their first
    three words", and only then change the prompt. That way the stricter
    criterion is written before I see whether it passes.
- **Rough no-results wording.** It says "in under $20", and "size than xl" is
  lowercased by `.capitalize()` in `agent.py::_no_results_message`. It's
  cosmetic, and criterion 2 is still met.
- **MCP:** only the main search call moved. `_no_results_message` still calls
  `search_listings` directly for its "drop one filter" hints. Moving it is a
  two-line change, but every retry would then start a server process, so I
  left it direct.
- **Trace prints on every run, not just with `--trace`,** because
  `trace.step()` always prints. It's harmless, but noisy in normal use.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
