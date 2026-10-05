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
