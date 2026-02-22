# Project Status & Roadmap

Reference: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (code-wise steps 1–10).

Pipeline step inputs/outputs: [docs/PIPELINE_STEPS.md](docs/PIPELINE_STEPS.md).

---

## What We Just Finished

- **Bulk enrichment run:** The pipeline loaded places from `data/input/יפן.csv`, called the Google Places API (Text Search → Place Details) for each, and wrote an intermediate JSON to `data/output/enriched_20260214_2129.json`.
- **Steps 1–4 are implemented and exercised:** Project scaffolding, config, load places (CSV/TXT), Google Places client, and batch enrich in `src/main.py` with debug JSON save. Each enriched record has `name`, `latitude`, `longitude`, `rating`, `user_ratings_count`, `reviews`, `types`, `address`, `place_id`.

---

## Completed Tasks

- [x] **Step 1 — Project scaffolding and config:** `config/`, `src/`, `data/input/`, `data/output/`, `tests/`; `config/settings.py` with dotenv, `GOOGLE_MAPS_API_KEY`, LLM keys, `PLACES_REQUEST_DELAY`, paths. No `.env.example` yet.
- [x] **Step 2 — Load places:** `src/load_places.py` — CSV (name/place/title + optional address) and TXT (one place per line).
- [x] **Step 3 — Google Places API client:** `src/google_places.py` — Text Search → Place Details, normalized dict, rate limiting via `settings.PLACES_REQUEST_DELAY`, error handling. Geocoding API fallback **not** implemented.
- [x] **Step 4 — Enrich all places (batch):** `src/main.py` — `enrich_places()`, `save_enriched_debug()`, `run_enrich()`; entrypoint is repo-root `main.py` (uses `INPUT_FILE` from `.env`).

---

## Unfinished Files & Logic (Exact Status)

| Item | Status |
|------|--------|
| **Step 5 — LLM categorization** | **Not started.** No `src/categorize.py`. Need: four categories (Restaurants, Street food, Shopping, Attractions), prompt using `name`/`types`/reviews, OpenAI or Anthropic call, normalize to one category, batch or single with order preserved, retries + default category on failure. |
| **Step 6 — Map category → icon color** | **Not started.** No mapping in `config/settings.py` or elsewhere. Plan: Restaurants→red, Street food→orange, Shopping→blue, Attractions→green. |
| **Step 7 — Master store & export CSV** | **Not started.** No `src/export.py` or `src/store.py`. Need: master store (e.g. CSV or SQLite) with Name, Latitude, Longitude, Category, Icon_Color (+ optional address, rating, place_id); merge/dedupe by place_id or name+address; regenerate single CSV `Name, Latitude, Longitude, Category, Icon_Color` to `data/output/mymaps_export_YYYYMMDD_HHMM.csv` (UTF-8). |
| **Step 8 — End-to-end pipeline & CLI** | **Partial.** `src/main.py` only does enrich; no categorize → store → export. No `scripts/` directory and no `scripts/run_agent.py`; no CLI that runs full flow (load → enrich → categorize → merge to store → regenerate CSV). |
| **Step 9 — Error handling & robustness** | **Partial.** Places client has try/except and logging; no retries with backoff (e.g. `tenacity`) for 429/5xx; no CSV output validation (missing lat/lng, category enum). |
| **Step 10 — Tests & sample data** | **Partial.** `data/input/places_sample.csv` not added. Only `tests/debug_google_places.py` (manual test). No `test_load_places.py`, `test_categorize.py`, `test_export.py`; no mocks for Google/LLM. |
| **`.env.example`** | **Missing.** Plan calls for placeholders: `GOOGLE_MAPS_API_KEY=`, `OPENAI_API_KEY=` or `ANTHROPIC_API_KEY=`. |

---

## Next Steps (When You Return)

1. **Add `src/categorize.py`** — Implement LLM categorization (Step 5): four categories, prompt from place `name`/`types`/reviews, call OpenAI or Anthropic, parse and normalize to one category; support batch with order preserved; retries and default category (e.g. Attractions) on failure.
2. **Add category → icon color mapping** — In `config/settings.py` or `src/export.py`: Restaurants→red, Street food→orange, Shopping→blue, Attractions→green (Step 6).
3. **Add `src/export.py` (and optional `src/store.py`)** — Master store (merge/dedupe by place_id or name+address), then regenerate one CSV with columns **Name, Latitude, Longitude, Category, Icon_Color** to `data/output/mymaps_export_YYYYMMDD_HHMM.csv` (Step 7).
4. **Wire full pipeline in `src/main.py`** — After enrich: categorize → map icon color → merge into master store → regenerate CSV. Keep existing `run_enrich()` for debug or split into `run_full_pipeline()` (Step 8).
5. **Add `scripts/` and `scripts/run_agent.py`** — CLI that takes input path (CSV/txt), optional output path, and calls the full pipeline; log progress (e.g. “Enriched 5/10”, “Categorized 10/10”) (Step 8).
6. **Harden errors** — Add retries with backoff (e.g. `tenacity`) for Places and LLM; validate export CSV (no missing lat/lng, category in {Restaurants, Street food, Shopping, Attractions}) (Step 9).
7. **Tests & sample data** — Add `data/input/places_sample.csv`; add `test_load_places.py`, `test_categorize.py`, `test_export.py` with mocks (Step 10).
8. **Add `.env.example`** — Placeholders for `GOOGLE_MAPS_API_KEY`, `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`, `INPUT_FILE` (and optional `PLACES_REQUEST_DELAY`).

---

## Technical Gotchas & Context

- **No API for My Maps:** The app never writes to My Maps. It only updates a master store and regenerates a CSV; you re-import that CSV into [Google My Maps](https://www.google.com/maps/d/) manually (first time: create map and map columns; later: re-import the new CSV to update).
- **Input file:** Pipeline input lives under **`data/steps/input/`** (e.g. put your CSV there; `INPUT_FILE` in `.env` is the filename). Step outputs go to **`data/steps/output/`** (`places_loaded.json`, `enriched.json`, `categorized.json`). See [docs/PIPELINE_STEPS.md](docs/PIPELINE_STEPS.md).
- **Places API field names:** Code uses `types` (list) and normalized keys like `user_ratings_count`; IMPLEMENTATION_PLAN overview mentions `native_types` — same data, different naming.
- **Enriched JSON is intermediate only:** `data/output/enriched_*.json` is for debugging. The canonical output for My Maps is the CSV from Step 7 (not yet implemented).
- **Geocoding fallback:** If Places returns no coordinates (e.g. address-only input), there is no Geocoding API fallback yet; optional per plan.
- **Secrets:** `.env` contains API keys. Do not commit it; add `.env` to `.gitignore` if not already. Use `.env.example` for documentation only.
- **Rate limiting:** `PLACES_REQUEST_DELAY` (default 0.5s) is applied between Place Details calls; ensure billing and quotas are set in Google Cloud for Places (and Geocoding if you add fallback).
