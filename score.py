"""
Scoring the five criteria from a set of runs. ← UNIT 4

run_eval.py leaves the verdict columns blank on purpose, because what counts as
a pass is whatever criteria.md says. This reads the sessions back and applies
those five rules.
"""

import re
import sys

from agent import run_agent
from scenarios import SCENARIOS
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

TRIES = 5


def sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s])


def score(session: dict, criterion: int, card_openings: list) -> bool:
    if criterion == 1:
        return not session["error"] and bool(session["fit_card"])
    if criterion == 2:
        return (
            bool(session["error"])
            and session["outfit_suggestion"] is None
            and session["fit_card"] is None
            and any(w in session["error"].lower() for w in ("ceiling", "size", "words"))
        )
    if criterion == 3:
        item = session["selected_item"]
        if not item or not session["search_results"]:
            return False
        if item["id"] != session["search_results"][0]["id"]:
            return False
        outfit = (session["outfit_suggestion"] or "").lower()
        key = max(re.findall(r"[a-z]{4,}", item["title"].lower()), key=len, default="")
        return key in outfit
    if criterion == 4:
        card = session["fit_card"] or ""
        price = f"{session['selected_item']['price']:.0f}" if session["selected_item"] else "x"
        opening = card.split(".")[0].strip().lower()
        unique = opening not in card_openings
        card_openings.append(opening)
        return sentences(card) <= 4 and price in card and unique
    if criterion == 5:
        ceiling = session["parsed"].get("max_price")
        asked = 45.0 if "45" in session["query"] else ceiling
        return (
            ceiling == asked
            and all(l["price"] <= ceiling for l in session["search_results"])
        )
    return False


def main():
    results = {}
    for scenario in SCENARIOS:
        number = scenario.get("criterion")
        if not number:
            continue
        wardrobe = get_empty_wardrobe() if scenario["wardrobe"] == "empty" else get_example_wardrobe()
        openings, passes = [], []
        for _ in range(TRIES):
            session = run_agent(scenario["query"], wardrobe)
            passes.append(score(session, number, openings))
        results[number] = passes
        print(f"criterion {number}: {sum(passes)}/{TRIES}  {['PASS' if p else 'FAIL' for p in passes]}")
    return results


if __name__ == "__main__":
    sys.exit(0 if main() else 0)
