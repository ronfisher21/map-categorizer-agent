"""
Step 6: Map category → icon for My Maps.
Reads categorized.json, adds an 'icon' field per place (one icon per category),
and saves to categorized_with_icons.json. Used so you can "Style by" that column in My Maps.
"""
import logging
from typing import Any

from config import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category → icon (for My Maps "Style by" column; one icon per category)
# ---------------------------------------------------------------------------
CATEGORY_TO_ICON: dict[str, str] = {
    "Restaurants": "restaurant",
    "Street food": "street_food",
    "Shopping": "shopping",
    "Attractions": "attraction",
    "Sweets": "sweets",
    "Cable": "cable",
    "Hotel": "hotel",
}
DEFAULT_ICON = "attraction"


def get_icon_for_category(category: str | None) -> str:
    """Return the icon identifier for a category. Unknown categories get DEFAULT_ICON."""
    if not category or not isinstance(category, str):
        return DEFAULT_ICON
    return CATEGORY_TO_ICON.get(category.strip(), DEFAULT_ICON)


def assign_icons(places: list[dict[str, Any]]) -> None:
    """Set place['icon'] for each place from place['category'] (mutates in place)."""
    for place in places:
        place["icon"] = get_icon_for_category(place.get("category"))
