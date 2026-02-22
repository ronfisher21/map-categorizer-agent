"""
LLM-based categorization of places into one of four categories for My Maps.
Sends places in batches; returns a dict mapping place name -> category.
"""
import json
import logging
import re
import time
from typing import Any

from config import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
CATEGORIES = ["Restaurants", "Street food", "Shopping", "Attractions", "Sweets", "Cable", "Hotel"]
DEFAULT_CATEGORY = "Attractions"

# Synonyms / typos → canonical category
_CATEGORY_ALIASES: dict[str, str] = {
    "restaurant": "Restaurants",
    "restaurants": "Restaurants",
    "street food": "Street food",
    "streetfood": "Street food",
    "shopping": "Shopping",
    "attraction": "Attractions",
    "attractions": "Attractions",
    "sweet": "Sweets",
    "sweets": "Sweets",
    "cable": "Cable",
    "hotel": "Hotel",
    "hotels": "Hotel",
}

# ---------------------------------------------------------------------------
# Quality color (green / yellow / red) from rating + review count
# ---------------------------------------------------------------------------
QUALITY_COLORS = ("green", "yellow", "red")


def get_quality_color(
    rating: float | None,
    user_ratings_count: int | None,
) -> str:
    """
    Return green / yellow / red from rating (1-5) and review count.
    Green: only when score >= 4.0 and enough reviews (>= 100).
    Red: low score (< 3.0), or medium score with very few reviews.
    Yellow: everything else.
    """
    s = float(rating) if rating is not None else 0.0
    r = int(user_ratings_count) if user_ratings_count is not None else 0

    if s >= 4.0:
        return "green" if r >= 100 else "yellow"
    if s < 3.0:
        return "red"
    # 3.0 <= s < 4.0: never green
    if r >= 100:
        return "yellow"
    return "red"


def assign_quality_colors(places: list[dict[str, Any]]) -> None:
    """Set place['quality_color'] for each place from rating and user_ratings_count."""
    for place in places:
        place["quality_color"] = get_quality_color(
            place.get("rating"),
            place.get("user_ratings_count"),
        )


def normalize_category(raw: str) -> str:
    """Map LLM output to exactly one of the five categories."""
    if not raw or not isinstance(raw, str):
        return DEFAULT_CATEGORY
    s = raw.strip()
    if not s:
        return DEFAULT_CATEGORY
    if s in CATEGORIES:
        return s
    key = s.lower()
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    for cat in CATEGORIES:
        if cat.lower() in key:
            return cat
    log.warning("Unrecognized category %r, defaulting to %s", s, DEFAULT_CATEGORY)
    return DEFAULT_CATEGORY


def _format_place_block(place: dict[str, Any], number: int) -> str:
    """Format one place for a batch prompt (with number)."""
    name = place.get("name") or ""
    types = place.get("types") or []
    types_str = ", ".join(types[:10]) if types else "unknown"
    rating = place.get("rating")
    count = place.get("user_ratings_count")
    rating_line = ""
    if rating is not None or count is not None:
        parts = []
        if rating is not None:
            parts.append(f"Rating: {rating}")
        if count is not None:
            parts.append(f"Review count: {count}")
        rating_line = " ".join(parts) + "\n"
    reviews = place.get("reviews") or []
    snippet = ""
    if reviews:
        first = (reviews[0] or "")[:400]
        snippet = f"Review snippet: {first}\n"
    return f"""--- Place {number} ---
Name: {name}
Types: {types_str}
{rating_line}{snippet}"""


def _build_batch_prompt(places: list[dict[str, Any]]) -> str:
    """Build one prompt for a batch of places; ask for JSON { "1": "Category", "2": "Category", ... }."""
    blocks = [_format_place_block(p, i + 1) for i, p in enumerate(places)]
    places_text = "\n".join(blocks)
    return f"""Classify each place below into exactly one category.

{places_text}

Categories (use exactly these): {', '.join(CATEGORIES)}.

Reply with a JSON object only. Keys are the place numbers as strings ("1", "2", "3", ...). Values are the category for that place. No other text.
Example: {{"1": "Restaurants", "2": "Shopping", "3": "Attractions"}}"""


def _parse_batch_response(raw: str, places: list[dict[str, Any]]) -> dict[str, str]:
    """
    Parse LLM response into {place_name: category}. Validates each value with normalize_category.
    Uses place number keys ("1", "2", ...) to match response to places by index.
    """
    result: dict[str, str] = {}
    raw = raw.strip()
    # Extract JSON (handle markdown code blocks)
    json_str = raw
    if "```" in raw:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if match:
            json_str = match.group(1).strip()
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        log.warning("Batch response JSON parse failed: %s. Raw: %s", e, raw[:200])
        for i, place in enumerate(places):
            name = place.get("name") or ""
            result[name] = DEFAULT_CATEGORY
        return result
    if not isinstance(parsed, dict):
        for i, place in enumerate(places):
            name = place.get("name") or ""
            result[name] = DEFAULT_CATEGORY
        return result
    for i, place in enumerate(places):
        name = place.get("name") or ""
        key = str(i + 1)
        raw_cat = parsed.get(key) or parsed.get(str(i)) or parsed.get(i + 1)
        result[name] = normalize_category(str(raw_cat) if raw_cat is not None else "")
    return result


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=settings.GEMINI_API_KEY,
    )
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200000,
    )
    raw = (response.choices[0].message.content or "").strip()
    return raw


def _call_llm(prompt: str) -> str:
    """Call the configured LLM (Gemini via OpenAI-compatible endpoint)."""
    if settings.GEMINI_API_KEY:
        return _call_openai(prompt)
    raise ValueError("No LLM API key set (GEMINI_API_KEY)")


def _categorize_batch(places: list[dict[str, Any]]) -> dict[str, str]:
    """Call LLM once for a batch; return {place_name: category} with validated categories."""
    prompt = _build_batch_prompt(places)
    raw = _call_llm(prompt)
    return _parse_batch_response(raw, places)


def categorize_places(places: list[dict[str, Any]]) -> dict[str, str]:
    """
    Categorize places in batches. Returns {place_name: category} with validated categories.
    Uses CATEGORIZE_BATCH_SIZE places per request; delay between requests per LLM_REQUEST_DELAY.
    """
    if not places:
        return {}
    batch_size = max(1, getattr(settings, "CATEGORIZE_BATCH_SIZE", 30))
    delay = max(0.0, settings.LLM_REQUEST_DELAY)
    combined: dict[str, str] = {}
    for start in range(0, len(places), batch_size):
        batch = places[start : start + batch_size]
        if start > 0 and delay > 0:
            time.sleep(delay)
        try:
            batch_result = _categorize_batch(batch)
            combined.update(batch_result)
            for place in batch:
                name = place.get("name") or ""
                cat = batch_result.get(name, DEFAULT_CATEGORY)
                log.info("Batch %d: %s → %s", (start // batch_size) + 1, name, cat)
        except Exception as e:
            log.exception("Batch failed (places %d-%d): %s", start + 1, start + len(batch), e)
            for place in batch:
                combined[place.get("name") or ""] = DEFAULT_CATEGORY
    return combined
