import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings

from src.assign_icons import assign_icons
from src.categorize import DEFAULT_CATEGORY, assign_quality_colors, categorize_places
from src.google_places import fetch_place_details
from src.load_places import load_places, load_enriched

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Step output paths (for running pipeline step-by-step)
# ---------------------------------------------------------------------------
def _step_path(filename: str) -> Path:
    return settings.STEPS_OUTPUT_DIR / filename


def save_step_output(data: list[dict[str, Any]], filename: str) -> Path:
    """Save step output to data/steps/output/<filename>."""
    path = _step_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Saved step output: %s (%d items)", path, len(data))
    return path


def load_step_output(filename: str) -> list[dict[str, Any]]:
    """Load step output from data/steps/output/<filename>."""
    path = _step_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Step output not found: {path}. Run the previous step first.")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    log.info("Loaded step output: %s (%d items)", path, len(data))
    return data


# ---------------------------------------------------------------------------
# Enrich (Google Places)
# ---------------------------------------------------------------------------
def enrich_places_from_list(places: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Enrich a list of place dicts (name, optional address) via Google Places API."""
    enriched: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for i, place in enumerate(places):
        name = place.get("name") or ""
        address = place.get("address")
        log.info("Enriched %d/%d: %s", i + 1, len(places), name)
        detail = fetch_place_details(name, address)
        if detail:
            enriched.append(detail)
        else:
            failed.append(place)
            log.warning("No details for: %s", name)
    return enriched, failed


def enrich_places(input_path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    places = load_places(input_path)
    return enrich_places_from_list(places)


def save_enriched_debug(enriched: list[dict[str, Any]], out_path: Path | None = None) -> Path:
    if out_path is None:
        out_path = settings.OUTPUT_DIR / f"enriched_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    log.info("Saved %d places to %s", len(enriched), out_path)
    return out_path


# ---------------------------------------------------------------------------
# Step runners (read/write step files so you can run one step at a time)
# ---------------------------------------------------------------------------
def run_step_load(input_path: str | Path) -> list[dict[str, Any]]:
    """Step 1: Load places from CSV/txt and save to data/steps/output/places_loaded.json."""
    places = load_places(input_path)
    save_step_output(places, settings.STEP_PLACES_LOADED)
    return places


def run_step_enrich(input_path: str | Path | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Step 2: Enrich places (from previous step file or input_path) and save to data/steps/output/enriched.json."""
    if input_path is None:
        places = load_step_output(settings.STEP_PLACES_LOADED)
    else:
        places = load_places(input_path)
    enriched, failed = enrich_places_from_list(places)
    if enriched:
        save_step_output(enriched, settings.STEP_ENRICHED)
    return enriched, failed


def run_step_categorize() -> list[dict[str, Any]]:
    """Step 3: Load enriched from data/steps/output/enriched.json, categorize, assign quality_color, save to categorized.json."""
    enriched = load_step_output(settings.STEP_ENRICHED)
    name_to_category = categorize_places(enriched)
    for place in enriched:
        place["category"] = name_to_category.get(place.get("name") or "", DEFAULT_CATEGORY)
    assign_quality_colors(enriched)
    save_step_output(enriched, settings.STEP_CATEGORIZED)
    return enriched


def run_step_assign_icons() -> list[dict[str, Any]]:
    """Step 4: Load categorized.json from data/steps/output/, add icon per category, save to categorized_with_icons.json."""
    places = load_step_output(settings.STEP_CATEGORIZED)
    assign_icons(places)
    save_step_output(places, settings.STEP_CATEGORIZED_WITH_ICONS)
    return places


# ---------------------------------------------------------------------------
# Full pipeline (legacy / all-in-one)
# ---------------------------------------------------------------------------
def run_enrich(input_path: str | Path, save_debug: bool = True) -> list[dict[str, Any]]:
    """Load already-enriched JSON from input_path, categorize, and optionally save debug JSON."""
    enriched = load_enriched(input_path)
    if enriched:
        name_to_category = categorize_places(enriched)
        for place in enriched:
            place["category"] = name_to_category.get(place.get("name") or "", DEFAULT_CATEGORY)
        assign_quality_colors(enriched)
        if save_debug:
            save_enriched_debug(enriched)
    return enriched


def run_full_pipeline(input_path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Run all steps in order, saving each step output. Returns (categorized with icons, failed from enrich)."""
    run_step_load(input_path)
    enriched, failed = run_step_enrich(input_path=None)
    if not enriched:
        return [], failed
    run_step_categorize()
    with_icons = run_step_assign_icons()
    return with_icons, failed
