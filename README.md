# Map Categorizer Agent

A Python agent that takes a list of locations, enriches them with Google Maps data (coordinates, reviews, details), classifies them with an LLM into custom categories, and exports a CSV ready for **Google My Maps** import.

## Categories

- **Restaurants** — sit-down dining
- **Street food** — stalls, markets, casual takeaway
- **Shopping** — retail, markets, malls
- **Attractions** — sights, museums, parks, landmarks

## Project Structure

```
google_maps_project/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .cursorrules             # Project conventions
├── .env.example              # Template for API keys (do not commit .env)
│
├── config/
│   └── __init__.py
│   └── settings.py           # Load env, API URLs, rate limits
│
├── src/
│   ├── __init__.py
│   ├── load_places.py        # Load places from CSV or text file
│   ├── google_places.py      # Google Places API client (fetch coords, reviews, details)
│   ├── categorize.py        # LLM classification (OpenAI/Anthropic)
│   ├── export.py             # Build CSV for Google My Maps
│   └── main.py               # Orchestrate: load → fetch → categorize → export
│
├── data/
│   ├── input/                # Your input place lists (CSV or .txt)
│   │   └── places_sample.csv
│   └── output/               # Generated CSV for My Maps
│       └── mymaps_export_YYYYMMDD_HHMM.csv
│
├── scripts/
│   └── run_agent.py          # CLI entry point (optional)
│
└── tests/
    ├── __init__.py
    ├── test_load_places.py
    ├── test_google_places.py
    ├── test_categorize.py
    └── test_export.py
```

## Quick Start

1. **Clone / open** this project and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Google Cloud & API keys**
   - Enable **Places API (New)** and **Geocoding API** in Google Cloud Console.
   - Create an API key and restrict it (HTTP referrer or IP if server-side).
   - Copy `.env.example` to `.env` and set:
     - `GOOGLE_MAPS_API_KEY=your_key`
     - `OPENAI_API_KEY=your_key` (or `ANTHROPIC_API_KEY` for Claude).

3. **Input**
   - Put a CSV with a `name` (or `place`) column, or a `.txt` with one place per line in `data/input/`.

4. **Run**
   ```bash
   python scripts/run_agent.py data/input/places_sample.csv
   ```
   Output CSV will be in `data/output/` with columns: **Name, Latitude, Longitude, Category, Icon_Color**.

5. **Import into Google My Maps**
   - Go to [Google My Maps](https://www.google.com/maps/d/), create a new map, **Import** → upload the CSV, map columns to Name / Lat / Long / Category (and optionally use Category for layer or style).

## Output CSV Format (Google My Maps)

| Name            | Latitude  | Longitude | Category   | Icon_Color |
|-----------------|-----------|-----------|------------|------------|
| Example Restaurant | 40.7128 | -74.0060  | Restaurants | red        |
| Night Market    | 25.0330   | 121.5654  | Street food | orange     |

- **Icon_Color**: Used to style pins in My Maps (e.g. red, blue, green, orange).

## Implementation Plan

See **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** for:
- Step-by-step code implementation order
- Google Cloud / Workspace setup (APIs, billing, keys)
- Rate limiting and error handling
- Testing and validation

## License

Use as you like; ensure you comply with Google Maps Platform and OpenAI/Anthropic ToS.
