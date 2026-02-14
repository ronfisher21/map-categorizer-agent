import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings

from src.google_places import fetch_place_details
from src.load_places import load_places

log = logging.getLogger(__name__)


def enrich_places(input_path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    places = load_places(input_path)
    enriched: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for i, place in enumerate(places):
        name = place.get("name") or ""
        address = place.get("address")
        log.info("Enriched %d/%d: %s", i, len(places), name)
        detail = fetch_place_details(name, address)
        if detail:
            enriched.append(detail)
        else:
            failed.append(place)
            log.warning("No details for: %s", name)

    return enriched, failed


def save_enriched_debug(enriched: list[dict[str, Any]], out_path: Path | None = None) -> Path:
    if out_path is None:
        out_path = settings.OUTPUT_DIR / f"enriched_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    log.info("Saved %d places to %s", len(enriched), out_path)
    return out_path


def run_enrich(input_path: str | Path, save_debug: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched, failed = enrich_places(input_path)
    if save_debug and enriched:
        save_enriched_debug(enriched)
    return enriched, failed
