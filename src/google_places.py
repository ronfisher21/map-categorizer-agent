import logging
import time
from typing import Any

import requests

from config import settings

log = logging.getLogger(__name__)

BASE = "https://places.googleapis.com/v1"
SEARCH_FIELDS = "places.id,places.displayName"
DETAILS_FIELDS = "id,displayName,location,formattedAddress,rating,userRatingCount,reviews,types"


def fetch_place_details(place_query: str, address: str | None = None) -> dict[str, Any] | None:
    query = place_query if not address else f"{place_query} {address}"
    place_id = _search_place(query)
    if not place_id:
        return None
    time.sleep(settings.PLACES_REQUEST_DELAY)
    return _place_details(place_id)


def _search_place(text: str) -> str | None:
    url = f"{BASE}/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": SEARCH_FIELDS,
    }
    payload = {"textQuery": text}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        places = data.get("places") or []
        if not places:
            log.warning("No results for query: %s", text)
            return None
        place = places[0]
        pid = place.get("id")
        name = place.get("name")
        if pid:
            return pid if pid.startswith("places/") else f"places/{pid}"
        if name and isinstance(name, str) and name.startswith("places/"):
            return name
        return None
    except requests.RequestException as e:
        log.exception("Places search failed for %s: %s", text, e)
        return None


def _place_details(place_id: str) -> dict[str, Any] | None:
    if not place_id.startswith("places/"):
        place_id = f"places/{place_id}"
    url = f"{BASE}/{place_id}"
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": DETAILS_FIELDS,
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        p = r.json()
        return _normalize_place(p)
    except requests.RequestException as e:
        log.exception("Place details failed for %s: %s", place_id, e)
        return None


def _normalize_place(p: dict) -> dict[str, Any]:
    name = _get_text(p.get("displayName")) or ""
    loc = p.get("location") or {}
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    reviews_raw = p.get("reviews") or []
    reviews = [_get_text(r.get("text")) or _get_text(r.get("originalText")) for r in reviews_raw[:5]]
    reviews = [t for t in reviews if t]
    types_list = p.get("types") or []
    return {
        "name": name,
        "latitude": lat,
        "longitude": lng,
        "rating": p.get("rating"),
        "user_ratings_count": p.get("userRatingCount"),
        "reviews": reviews,
        "types": types_list,
        "address": _get_text(p.get("formattedAddress")) or "",
        "place_id": p.get("id") or "",
    }


def _get_text(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) and "text" in obj:
        return obj.get("text")
    return None
