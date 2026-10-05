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

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable

PRICE_RE = re.compile(r"(?:under|below|less than|max|up to)?\s*\$?\s*(\d+(?:\.\d{1,2})?)\s*(?:dollars|bucks)?\b", re.I)
SIZE_RE = re.compile(r"\bsize\s+([a-z0-9/]+)\b|\b(xs|s|m|l|xl|xxl)\b(?!\w)", re.I)
PARSE_NOISE = re.compile(r"\b(under|below|less than|max|up to|size)\b|\$\s*\d+(\.\d+)?|\b\d+(\.\d+)?\s*(dollars|bucks)\b", re.I)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a price ceiling out of plain language.

    Regex rather than a model call: parsing the same sentence twice has to give
    the same answer, and a model call here would add latency and variance to
    every run for nothing.
    """
    price = None
    price_match = re.search(r"(?:under|below|less than|max|up to)\s*\$?\s*(\d+(?:\.\d{1,2})?)|\$\s*(\d+(?:\.\d{1,2})?)", query, re.I)
    if price_match:
        price = float(price_match.group(1) or price_match.group(2))

    size = None
    size_match = re.search(r"\bsize\s+([a-z0-9/]+)", query, re.I)
    if size_match:
        size = size_match.group(1).upper()
    else:
        bare = re.search(r"\b(xs|xl|xxl|s|m|l)\b", query, re.I)
        if bare:
            size = bare.group(1).upper()

    description = PARSE_NOISE.sub(" ", query)
    if size:
        description = re.sub(rf"\b{re.escape(size)}\b", " ", description, flags=re.I)
    description = re.sub(r"[,\s]+", " ", description).strip()

    return {"description": description, "size": size, "max_price": price}


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    try:
        count += 1
        trace.check_iterations(count)
        session["parsed"] = parse_query(query)

        count += 1
        trace.check_iterations(count)
        session["search_results"] = search_listings(**session["parsed"])

        if not session["search_results"]:
            session["error"] = _nothing_found(session["parsed"])
            return session

        session["selected_item"] = session["search_results"][0]

        count += 1
        trace.check_iterations(count)
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )

        if not (session["outfit_suggestion"] or "").strip():
            session["error"] = (
                "Found "
                f"{session['selected_item']['title']} but couldn't come up with an "
                "outfit for it, so there's no fit card."
            )
            return session

        count += 1
        trace.check_iterations(count)
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )

    except ModelUnavailable as exc:
        session["error"] = f"The model couldn't be reached: {exc}"

    return session


def _nothing_found(parsed: dict) -> str:
    """The message for the empty-search branch, naming what to relax."""
    relax = []
    if parsed.get("max_price") is not None:
        relax.append(f"raising the ${parsed['max_price']:.0f} ceiling")
    if parsed.get("size"):
        relax.append(f"dropping the size {parsed['size']} filter")
    relax.append(f"using different words than \"{parsed['description']}\"")
    return "Nothing in the listings matches that. Try " + ", or ".join(relax) + "."


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
