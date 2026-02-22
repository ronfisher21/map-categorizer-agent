"""
Load environment and expose settings for the Map Categorizer Agent.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths (project root = parent of config/)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Steps hierarchy: input and output for pipeline steps
STEPS_DIR = DATA_DIR / "steps"
STEPS_INPUT_DIR = STEPS_DIR / "input"
STEPS_OUTPUT_DIR = STEPS_DIR / "output"
STEPS_INPUT_DIR.mkdir(parents=True, exist_ok=True)
STEPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pipeline uses steps/input for CSV/txt and steps/output for step JSONs
INPUT_DIR = STEPS_INPUT_DIR 
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE: str = os.getenv("INPUT_FILE", "").strip()
STEP_PLACES_LOADED = "places_loaded.json"
STEP_ENRICHED = "enriched.json"
STEP_CATEGORIZED = "categorized.json"

# ---------------------------------------------------------------------------
# Google Maps
# ---------------------------------------------------------------------------
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# LLM (use one or both)
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Optional: rate limiting and behavior
# ---------------------------------------------------------------------------
PLACES_REQUEST_DELAY: float = float(os.getenv("PLACES_REQUEST_DELAY", "0.5"))
# Delay between LLM requests (seconds). 6.0 = 10 RPM (Gemini free tier).
LLM_REQUEST_DELAY: float = float(os.getenv("LLM_REQUEST_DELAY", "6.0"))
# Number of places per batch when categorizing (one API call per batch).
CATEGORIZE_BATCH_SIZE: int = int(os.getenv("CATEGORIZE_BATCH_SIZE", "30"))


def get_llm_key() -> str:
    """Return the first available LLM API key (OpenAI preferred)."""
    if OPENAI_API_KEY:
        return OPENAI_API_KEY
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    return ""


def mask_key(key: str, visible: int = 4) -> str:
    """Return a masked version of an API key for safe logging."""
    if not key or len(key) <= visible:
        return "***"
    return key[:visible] + "*" * (len(key) - visible)
