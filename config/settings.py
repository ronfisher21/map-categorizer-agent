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
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
INPUT_FILE: str = os.getenv("INPUT_FILE", "").strip()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Google Maps
# ---------------------------------------------------------------------------
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# LLM (use one or both)
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()

# ---------------------------------------------------------------------------
# Optional: rate limiting and behavior
# ---------------------------------------------------------------------------
PLACES_REQUEST_DELAY: float = float(os.getenv("PLACES_REQUEST_DELAY", "0.5"))


def get_llm_key() -> str:
    """Return the first available LLM API key (OpenAI preferred)."""
    if OPENAI_API_KEY:
        return OPENAI_API_KEY
    if ANTHROPIC_API_KEY:
        return ANTHROPIC_API_KEY
    return ""


def mask_key(key: str, visible: int = 4) -> str:
    """Return a masked version of an API key for safe logging."""
    if not key or len(key) <= visible:
        return "***"
    return key[:visible] + "*" * (len(key) - visible)
