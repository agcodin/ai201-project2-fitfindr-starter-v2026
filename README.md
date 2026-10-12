# FitFindr

Aryan Gaur — AI201 Project 3

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
> **The rest of this file is your submission.**

---

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a request for a secondhand clothing item, like "vintage graphic tee under $30, size M", and works out what to do with it. It searches 40 thrift listings for something that fits the description, the size and the price ceiling, looks at what the user already owns, suggests how to wear the find with those pieces, and writes a caption they could post about it. When nothing in the listings matches, it stops after the search and says which part of the request to loosen rather than inventing an item to style.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the 40 listings in `data/` by size and price, scores what is left by keyword overlap against the description, and returns the best matches first. No model call.
- **Inputs:** `description` (str, required), `size` (str or None), `max_price` (float or None)
- **Returns:** A list of listing dicts, at most `config.SEARCH_RESULT_LIMIT` of them, ordered by score descending. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`.
- **When it has nothing:** An empty list `[]`. Never None, never an exception. This is what the loop branches on.

Sizes are matched by family, not by substring. The data holds letter sizes (`M`, `S/M`, `XL (oversized)`), waist sizes (`W30`, `W30 L30`), shoe sizes (`US 8.5`) and `One Size`. A requested letter size matches a listing whose size contains that letter token, so `M` matches `M`, `S/M` and `M/L`, and it also matches anything labelled `One Size`. It does not match `XL`, and it does not match `US 9` or `W30`, which a plain `in` test would wrongly accept.

### `suggest_outfit`

- **What it does:** Asks the model how to wear one listing, naming pieces from the user's wardrobe when there are any.
- **Inputs:** `new_item` (dict, a listing), `wardrobe` (dict with an `items` key holding a list of wardrobe-item dicts, possibly empty)
- **Returns:** A non-empty str holding one or two outfit suggestions. With a wardrobe, it names specific owned pieces by name. With an empty wardrobe, it returns general styling advice for the item instead.
- **When it has nothing:** An empty wardrobe is not an error, so it still returns advice. If the model cannot be reached, `generate()` raises `ModelUnavailable` and the loop catches it.

### `create_fit_card`

- **What it does:** Writes a two-to-four sentence caption about the find, in the voice of someone posting it.
- **Inputs:** `outfit` (str, the output of `suggest_outfit`), `new_item` (dict, a listing)
- **Returns:** A str caption of two to four sentences, mentioning the item, its price and its platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace, it returns the string `"No outfit to caption yet — suggest_outfit returned nothing."` rather than raising or calling the model.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, write a message into `session["error"]` naming the constraint to relax (the size, the price ceiling, or the keywords, whichever were set) and return the session without calling the other two tools. Otherwise take the first result as `session["selected_item"]` and continue to `suggest_outfit`, then `create_fit_card`.

A second branch sits inside the first path. If `suggest_outfit` comes back empty or whitespace, the loop stops there and sets `session["error"]` instead of handing an empty string to `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. One pattern pulls a price off `under $30`, `below 30` or `$30`, another pulls a size off `size M` or a bare `XL`, and the rest of the words become the description after the stop words (`looking`, `for`, `under`, `size`) are dropped. I chose regex over asking the model because parsing is deterministic and a model call here would make every run slower and non-repeatable for no gain.

**What moves through the session:** `query` is set by `new_session`, then `parsed` from `parse_query`, then `search_results` from `search_listings`, then `selected_item` (the first result), then `outfit_suggestion`, then `fit_card`. Each tool reads its input back out of the session rather than from a local variable, so a run that stops early leaves every later field as None.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the white butterfly print baby tee with the baggy straight-leg dark wash jeans and chunky white sneakers for an effortless Y2K contrast of fitted and loose silhouettes. Layer the vintage black denim jacket on top and add the black crossbody bag to complete the casual, nostalgic look.

Alternatively, tuck the baby tee into the wide-leg khaki trousers secured with the brown leather belt for a softer, earth-toned palette. Slip into the black combat boots and throw on the black cropped zip hoodie to give the outfit an edgy, grunge finish.

  Fit card: I am obsessed with this butterfly print baby tee I just grabbed on depop for $18. It is in amazing shape and has the best Y2K fit. You can dress it down with baggy jeans or lean into an edgy grunge vibe with some combat boots. Shoot me a message if you want to grab it.
```

The other path, where the branch fires:

```
$ python agent.py

=== A query it can't ===
  stopped: Nothing in the listings matches that. Try raising the $5 ceiling, or dropping the size XXS filter, or using different words than "designer ballgown".
  fit_card is None — it should still be None here
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30)[:2])"

[{'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Tuck the white ribbed tank top into the vintage Levi's 501 jeans, adding the brown leather belt and chunky white sneakers. Layer the vintage black denim jacket on top and finish with the black crossbody bag.

Pull the oversized grey crewneck sweatshirt over the vintage Levi's 501 jeans, cinched at the waist with the brown leather belt, and lace up the black combat boots. Sling the black crossbody bag across your chest to complete the look.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Scored this 2003 tour bootleg tee and it's already my favorite piece for throwing on with baggy jeans or wide-leg trousers. Grabbed it on Depop for $24 and the vintage wash is just right. It's in really good condition and the graphic has that perfectly faded grunge look. Hit me up if you want the outfit details.
```

The guard case, with nothing to caption:

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"

No outfit to caption yet — suggest_outfit returned nothing.
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* I gave Claude the `search_listings` spec and asked it to write the size filter.
- *What came back:* A plain substring test, `size.lower() in listing["size"].lower()`. It passes the obvious cases and the docstring warns about exactly this.
- *What I changed:* I checked it against the real sizes in the data. `"s" in "us 9"` is True and `"l" in "xl"` is True, so a request for a small top returns shoes. I replaced it with `size_matches`, which splits the listing size into tokens on slashes and spaces, compares letter sizes as whole tokens, treats "One Size" as matching any letter request, and keeps waist and shoe sizes in their own families. That rule is written into the Tool Inventory above because it is part of the spec, not an implementation detail.

**Moment 2**

- *What I asked for:* I had Claude write the `create_fit_card` prompt from my criterion, which says every card has to name the item's price.
- *What came back:* Cards that read well but spelled the price out, like "listed on Depop for eighteen dollars".
- *What I changed:* That would fail my own criterion 4, since a check for the price would be looking for "18". I made the system prompt ask for the price as digits with a dollar sign. Five runs later every card contains the numeral, and the sentence count is still inside the four-sentence limit.

---

## Run Log — Before

`python run_eval.py --label before` ran all six scenarios five times each, cache off, writing `results/run_2026-10-12_0157_before.md`. The five criteria were then scored against the rules in `criteria.md` by `score.py::score`, which reads each session back and applies them.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Found item is the item the outfit describes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card short, names the price, distinct openings | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling never exceeded | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Real output from try 1, produced by `agent.py::run_agent` over `tools.py` and `mcp_server.py`.

Criterion 1, the happy path:

```
selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
search_results: 10

Found this Y2K butterfly print baby tee on depop and it is in such good condition. I love balancing the fitted top with some baggy dark wash jeans and a black denim jacket. Grabbed it for $18.00 and it's already my new favorite piece for everyday outfits.
```

Criterion 2, the branch, where both later fields stay None:

```
stopped: Nothing in the listings matches that. Try raising the $5 ceiling, or dropping the size XXS filter, or using different words than "designer ballgown".
outfit_suggestion: None
fit_card: None
```

Criterion 5, the ceiling on `leather boots under $45`, parsed as 45.0 with every result at or under it:

```
Leather Belt — Brown, Braided | accessories | $12.00
Mini Shoulder Bag — Tan Leather | accessories | $38.00
Suede Chelsea Boots — Tan | shoes | $44.00
```

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET | 5 of 5 tries returned a fit card with no error set. The target allowed one failure and none happened. |
| 2 | Impossible query stops before the second tool | 5 of 5 | MET | 5 of 5. I checked all three conditions, not just the message, so a try only passed when `outfit_suggestion` and `fit_card` were both still None and the message named a constraint. |
| 3 | Found item is the item the outfit describes | 5 of 5 | MET | 5 of 5. The id comparison is the easy half. I also checked that the longest word in the item title appears in the outfit text, which is what catches a right id with a prompt built from something else. |
| 4 | Fit card short, names the price, distinct openings | 5 of 5 | MET | 5 of 5 on all three halves. Every card was 4 sentences or fewer, every one held the price as digits, and the five opening sentences were all different at temperature 0.9 with the cache off. |
| 5 | Price ceiling never exceeded | 5 of 5 | MET | 5 of 5. Both halves held, the parse read 45.0 out of "under $45" and no returned listing cost more than that. |

**Nothing missed, which means my targets were safe.** Four of the five test things my own deterministic code does, and deterministic code either works on every try or none of them. Criterion 2 compares a list length, criterion 3 compares two ids, criterion 5 compares floats. The only criterion with real variance in it is 4, and I wrote it loosely enough that a four-sentence limit and a price in digits were easy for the model to satisfy once the prompt asked for both.

**The one I would tighten, and to what.** Criterion 1 says a matching query completes all three tools, and it never asked whether the item that came back was the right kind of thing. I would rewrite it as "for 5 of 5 queries that name an item type, the top result is in the matching category". That is the failure I actually found this unit, and my criteria could not see it. Searching `leather boots under $45` completed all three tools, passed criterion 1, and handed the user a braided belt.

**The diagnosis for that failure, since the criteria did not catch it.** The stage is retrieval, inside `search_listings`. Every field was pooled into one string and scored by plain keyword overlap, so a term matching a material counted exactly as much as a term naming the garment. The belt is titled "Leather Belt — Brown, Braided" and the query was "leather boots", so the belt scored on "leather" while the Chelsea boots scored on "boots", and the belt won the tie on price. Nothing about the loop or the prompts was involved.

## Loop Trace

One full run with the MCP call in it, from `python app.py ask 'vintage graphic tee under $30' --trace`, printed by `trace.py::step`.

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (over MCP)
      in:  dict with keys: description, size, max_price
      out: 10 listings
[3] select item
      out: Y2K Baby Tee — Butterfly Print
      →    branch: results found, continuing to suggest_outfit
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print, 10 wardrobe items
      out: Pair the white butterfly print baby tee with the baggy straight-leg dark wash jeans and chunky white sneakers …
[5] create_fit_card
      out: I am obsessed with this butterfly print baby tee I just grabbed on depop for $18. It is in amazing shape and h…
```

Step 2 is the MCP call. `search_listings` is registered in `mcp_server.py` and reached through `mcp_client.call_tool`, so the agent no longer imports the function it is calling. The return value did not change when I moved it, which is what the starter said to check.

**The three failure modes, triggered on purpose.**

Empty search, the branch in criterion 2:

```
[2] search_listings (over MCP)
      out: 0 listings
[3] branch
      out: Nothing in the listings matches that. Try raising the $5 ceiling, or dropping the size XXS filter, or using different words than "designer ballgown".
      →    search came back empty, stopping before suggest_outfit
```

Empty wardrobe, run with `--empty-wardrobe`. `suggest_outfit` switches prompts rather than failing, and describes pieces by type instead of naming items the user does not own:

```
Layer the cropped jacket over an oversized graphic t-shirt in washed black, paired with slouchy forest green parachute pants and scuffed white canvas sneakers.
```

Model unreachable, triggered with a deliberately wrong key in the environment:

```
[4] model unavailable
      out: The model couldn't be reached: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
      →    caught, returning the session instead of raising
fit_card: None
```

A fourth path exists for MCP itself. `run_agent` catches `MCPError` the same way, so a server that will not start produces a message in the session rather than a stack trace.

## The Improvement

**What I changed:** the scoring inside `search_listings`. It used to pool the title, description, category, style tags, colors and brand into one string and count matching words. Now a match in the title or the category and style tags is worth 3, a match anywhere else is worth 1, and the last meaningful word of the query, which is almost always the item type, adds 6 when it appears in the title or category. One change, in one function.

**Why I picked it:** the diagnosis above pointed at exactly this. Flat scoring cannot tell a material from a garment, and weighting the item type is the smallest change that can. I did not touch the loop, the prompts or the parse, because none of them were implicated.

### Run Log — After

`python run_eval.py --label after`, writing `results/run_2026-10-12_0204_after.md`, scored the same way.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Found item is the item the outfit describes | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card short, names the price, distinct openings | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling never exceeded | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help?** It helped the agent and it moved none of my criteria, which is the honest answer and an uncomfortable one. All five were already at 5 of 5, so there was no room above them.

To measure it at all I had to write a check my criteria do not contain. I ran eight probe queries that name an item type and counted how often the top result was in the matching category, against the old scoring and the new one.

| | Top result in the right category |
|---|---|
| Before | 6 of 8 |
| After | 7 of 8 |

The query from the diagnosis changed hands. `leather boots under $45` now returns Suede Chelsea Boots first instead of the braided belt, and `denim jacket` returns the Denim Jacket rather than the Denim Vest.

That gap between a real improvement and a flat scoreboard is the finding. My criteria measured whether the pipeline ran, not whether it was right, and a system can go from wrong to right without any of them noticing.

## What's Still Broken

**No criterion was missed, so nothing here is a miss.** These are the failures the test found anyway.

**The search has no idea what words mean.** `a warm coat` returns nothing, because no listing contains the word coat, and the three jackets are tagged outerwear. `vintage t-shirt` returns a polo shirt first, since "shirt" is in the title and "t-shirt" is not a word the matcher knows. The fix is a small synonym map from everyday words to the categories and tags the data uses, probably ten entries. I stopped because the unit allows one improvement and I had spent it on scoring, and a second change made in the same pass would leave me unable to say which one moved the probes from 6 to 7.

**Probe query 8 of 8 still fails.** `corduroy pants` returns the Corduroy Wide-Leg Pants second, behind another corduroy item, because the head-word bonus fires for both and the tie breaks on price. Ranking ties by price is a decision I never thought about, and it is now load bearing.

**My criteria cannot see the thing I fixed.** That is the real gap. Criterion 1 passes whenever the three tools complete, and completing with the wrong item looks identical to completing with the right one. Next unit the first thing I would change is adding the category check to criterion 1 rather than keeping it as a probe script on the side.

**Moment 3**

- *What I asked for:* in unit 4 I gave Claude the failing query `leather boots under $45`, the three results it returned, and the scoring code, and asked for possible causes without ranking them.
- *What came back:* three, the keyword matcher weighting all fields equally, the price tiebreak favouring cheap accessories, and the category field being ignored.
- *What I changed:* I tested the first by weighting title and category matches above description matches, which was not enough on its own, since the belt's title also contains "leather". Adding a bonus for the query's last meaningful word, which is the item type, is what moved the boots to first.


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
