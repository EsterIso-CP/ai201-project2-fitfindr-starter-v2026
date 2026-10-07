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

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

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

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
