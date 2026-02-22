import logging
import os
from pathlib import Path

from config import settings
from src.main import (
    run_step_load,
    run_step_enrich,
    run_step_categorize,
    run_full_pipeline,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_DIR = settings.INPUT_DIR

# Run only one step: RUN_STEP=load | enrich | categorize | all
# - load: load CSV/txt from data/steps/input/ → save to data/steps/output/places_loaded.json
# - enrich: read places_loaded.json → Google Places → save to data/steps/output/enriched.json
# - categorize: read enriched.json → LLM → save to data/steps/output/categorized.json
# - all (default): run load → enrich → categorize, saving each step
RUN_STEP = os.getenv("RUN_STEP", "all").strip().lower()


def main() -> None:
    input_path = INPUT_DIR / settings.INPUT_FILE
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path} (set INPUT_FILE in .env)")

    if RUN_STEP == "load":
        places = run_step_load(input_path)
        print(f"Step 1 (load): saved {len(places)} places to {settings.STEPS_OUTPUT_DIR / settings.STEP_PLACES_LOADED}")
    elif RUN_STEP == "enrich":
        # Pass input_path so you can run enrich alone (loads from CSV). Or use None to read from steps/places_loaded.json.
        enriched, failed = run_step_enrich(input_path=input_path)
        print(f"Step 2 (enrich): {len(enriched)} enriched, {len(failed)} failed → {settings.STEPS_OUTPUT_DIR / settings.STEP_ENRICHED}")
    elif RUN_STEP == "categorize":
        categorized = run_step_categorize()
        print(f"Step 3 (categorize): {len(categorized)} with categories → {settings.STEPS_OUTPUT_DIR / settings.STEP_CATEGORIZED}")
    else:
        categorized, failed = run_full_pipeline(input_path)
        print(f"Full pipeline: {len(categorized)} categorized, {len(failed)} failed at enrich.")


if __name__ == "__main__":
    main()
