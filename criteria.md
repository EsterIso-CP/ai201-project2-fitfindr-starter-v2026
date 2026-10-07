# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Search is a plain keyword match, so a phrasing like "retro band shirt" can miss a listing tagged "vintage graphic tee" even though a person would call it a match. Two of the three tools also call a model, which can time out or return an empty string. I'd rather set an honest 4 of 5 and see which phrasings fail than claim 5 of 5 and hide that. I'll run this with five different phrasings, not the same query five times.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never touches the model. `search_listings` is plain Python and returns `[]` for the same input every time, so the stop is a plain `if` and there's no randomness to excuse a miss. A failure here is a bug, not variance. "Naming what to change" means the message points at the specific constraint that was too tight (the price ceiling, the size, or the keywords), not just "no results."

---

## 3. The selected item is the one the next tool receives

In 5 of 5 tries on a matching query, the listing `id` in
`session["selected_item"]` equals the `id` of the dict that `suggest_outfit`
received and the dict that `create_fit_card` received, and it equals the `id`
of the first element of the `search_listings` result. I'll check this by
logging the id at each handoff and comparing them. As a second check, the
price in the fit card must equal `selected_item["price"]`.

**Why this target:**
There's no model in the handoff. It's just passing a variable, so any mismatch is a bug: a stale item, a re-search that returned a different first result, or a wrong index. I'm not allowing a 4 of 5 here because one mismatch means the agent talked about the wrong item, which looks like a model hallucination when it's really a state failure.

---

## 4. The fit card is a caption and varies between runs

Running `create_fit_card` five times on the same item and outfit:
(a) in at least 4 of 5 runs the caption is 2–4 sentences, contains the item's
price once and its platform once; and
(b) no two of the five captions are word-for-word identical.
I'll check both with string tests, not by reading.

**Why this target:**
Different wording is expected from a model call, so I'm not checking the wording. I'm checking what I'd be unhappy to see. Length, price, and platform are things the prompt asks for but the model may drift on, so (a) allows one miss. Identical captions are different: they mean `CACHE_ENABLED` is on or `TEMPERATURE` is 0.0, which is a config bug and not model variance, so (b) allows no repeats.

---

## 5. Filters are respected

Given 5 queries that each include a `size` and a `max_price`, zero returned
listings violate either filter: every `price` is at most `max_price`, and every
size matches by the whole-token rule in the Tool Inventory (so "S" never
returns "US 9" or "XS"). 5 of 5 queries, zero violations.

**Why this target:**
This is deterministic code, so I don't allow any violations. A single shoe in a "small top" search makes the whole agent look broken, and it would quietly cost me in unit 4 when I test criterion 1. I chose this over the empty-wardrobe path because the size substring bug is the most likely mistake in this codebase.
---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
