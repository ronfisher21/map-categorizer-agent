import logging
from pathlib import Path

from config import settings
from src.main import run_enrich

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_DIR = settings.INPUT_DIR


def main() -> None:
    input_path = INPUT_DIR / settings.INPUT_FILE
    enriched, failed = run_enrich(input_path)
    print(f"Enriched: {len(enriched)}, Failed: {len(failed)}")


if __name__ == "__main__":
    main()
