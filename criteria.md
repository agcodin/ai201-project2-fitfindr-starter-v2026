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
My search is keyword overlap against the title, description and style tags, with no stemming and no synonyms, so phrasing decides whether anything comes back. "Graphic tee" hits the listings that use the word tee, and "t-shirt" may not. I allow one failure in five because the parse is regex and a query written in an order I did not anticipate can leave a stray word in the description that scores everything to zero.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path has no model call in it, so nothing about it varies between runs. An empty list is an empty list, and the branch that reads it is a comparison in my own code. If this ever came out at 4 of 5 it would mean the loop itself is nondeterministic, which would be a worse problem than the one the criterion is checking.

---

## 3. The item that search found is the item the outfit describes

For 5 runs on queries that match, the `title` of `session["selected_item"]` is the same listing the outfit text talks about, and `session["selected_item"]["id"]` equals the id of `session["search_results"][0]`, on 5 runs out of 5.

**Why this target:**
State dropping between tools is the failure this project is built around, and it does not look like a state bug from the outside. If the wrong item reaches `suggest_outfit`, the outfit reads perfectly well, just about a different garment. Comparing ids catches the plumbing, and reading the outfit text catches the case where the id is right and the prompt was built from something else. 5 of 5 because this is my own code passing a dict to itself, with no model involved in the comparison.

---

## 4. The fit card is specific to the item and short enough to post

Across 5 different items, every fit card is 4 sentences or fewer and names that item's price, and no two cards share their opening sentence. 5 of 5 on length and price, 5 of 5 distinct openings.

**Why this target:**
The caption calls the model at temperature 0.9, so I cannot ask for exact words. I can ask for the things I would be unhappy to lose. A card that runs past four sentences is a product description rather than a caption, and a card that omits the price is useless for a thrift find where the price is the point. The distinct-openings check is there because repeated openings are what a cached or zero-temperature run looks like, and it would be easy to mistake that for the model being boring.

---

## 5. The price ceiling is never exceeded

For 5 queries that name a price ceiling, no listing in `session["search_results"]` costs more than the ceiling, and the ceiling the agent parsed matches the number in the query, on 5 runs out of 5.

**Why this target:**
This is the one that silently produces wrong answers rather than visible failures. A regex that misses `$30` gives the user results with no ceiling at all and nothing in the output says so, which is exactly the PowerShell quoting trap `RUNNING.md` warns about. Both halves need checking, because a filter that works on a price the parse got wrong is still wrong. 5 of 5, since both the parse and the filter are deterministic code I wrote.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. The fit card is specific to the item and short enough to post

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
