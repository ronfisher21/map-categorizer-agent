# Implementation Plan: Map Categorizer Agent

This document gives a **code-wise** implementation order and a **Google Workspace / Cloud** walkthrough.

---

## Service overview: two use cases

The service keeps a **master list** of all your categorized places. A single **My Maps export CSV** is regenerated from that list whenever you add places. You then **manually re-import** that CSV into Google My Maps to update your map.

| Use case | Input | What the pipeline does | Your manual step |
|----------|--------|-------------------------|------------------|
| **First use (bulk)** | Full list (e.g. Google Takeout "Saved" CSVs) | Load → enrich (Places API) → categorize (LLM) → **save all to master store** → **regenerate CSV** | Import the CSV into My Maps (create map, map columns, style by category). |
| **Future use (single place)** | One place (e.g. sent via WhatsApp or CLI) | Resolve place → same enrich + categorize → **append to master store** → **regenerate CSV** | When you want the map updated: re-import the new CSV into My Maps (replace layer or create new import). |

There is **no API to push into My Maps**; the flow is always: pipeline updates the master store → regenerate one CSV → you re-import that file into My Maps when you want.

---

## Part A: Google Cloud / Workspace Walkthrough

### 1. Create or select a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. **Select a project** or **Create project** (e.g. `map-categorizer-agent`).
3. Ensure **billing** is enabled (required for Places API; free tier has quotas).

### 2. Enable required APIs

1. In the console: **APIs & Services** → **Library**.
2. Enable:
   - **Places API (New)** — place search, details, photos, reviews.
   - **Geocoding API** — fallback to get lat/lng from address if you only have addresses.
3. Wait a minute for propagation.

### 3. Create and restrict an API key

1. **APIs & Services** → **Credentials** → **Create credentials** → **API key**.
2. Copy the key; use it as `GOOGLE_MAPS_API_KEY` in `.env`.
3. **Edit API key** → **Application restrictions**:
   - For local scripts: **None** (or **IP addresses** if you know your IP).
   - For production: **IP addresses** or **HTTP referrers**.
4. **API restrictions**: **Restrict key** → select only **Places API (New)** and **Geocoding API** to limit exposure.

### 4. Google My Maps — manual re-import (after each run)

- The agent does **not** write to My Maps via API. It writes to a **master store** and **regenerates one CSV** in `data/output/`.
- **First time:** After the first bulk run, open [Google My Maps](https://www.google.com/maps/d/) → **Create new map** → **Import** → upload the generated CSV (e.g. `mymaps_export_YYYYMMDD_HHMM.csv`) → map columns (Name, Latitude, Longitude, Category, Icon_Color) → style by Category.
- **Later (after adding more places):** When you want your map updated, **re-import** the latest CSV from `data/output/` into the same map (e.g. add as new layer or replace the layer). So: regenerate CSV → download/open the new file → Import again in My Maps.

---

## Part B: Code-Wise Implementation Steps

Implement in this order so each step can be tested before moving on.

### Step 1: Project scaffolding and config

**Tasks:**

1. Create directories: `config/`, `src/`, `data/input/`, `data/output/`, `scripts/`, `tests/`.
2. Add `__init__.py` in `config/` and `src/`.
3. Create `.env.example` with placeholders:
   - `GOOGLE_MAPS_API_KEY=`
   - `OPENAI_API_KEY=` or `ANTHROPIC_API_KEY=`
4. Implement `config/settings.py`:
   - Load variables with `python-dotenv`.
   - Expose `GOOGLE_MAPS_API_KEY`, LLM key, and optional settings (e.g. rate limit delay, output dir).

**Validation:** Import `config.settings` and print that the API key is set (masked).

---

### Step 2: Load places from CSV or text

**File:** `src/load_places.py`

**Tasks:**

1. Accept input path (CSV or `.txt`).
2. **CSV:** Require a column like `name` or `place`; normalize to a list of strings (place names or addresses).
3. **TXT:** One place per line; strip blanks and comments if you like.
4. Return a simple structure, e.g. `list[dict]` with `{"name": "..."}` or `list[str]`.

**Validation:** Unit test with a small `data/input/places_sample.csv` and a `.txt` file.

---

### Step 3: Google Places API client

**File:** `src/google_places.py`

**Tasks:**

1. Use **Places API (New)**:
   - [Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search) (or Find Place from Text) to get `place_id` from name/address.
   - [Place Details](https://developers.google.com/maps/documentation/places/web-service/place-details) to get:
     - `location` (lat/lng)
     - `reviews` (sample of reviews)
     - `user_ratings_total`, `rating`
     - `displayName`, `types` (or `primaryType`), `formattedAddress`, etc.
2. Implement a function, e.g. `fetch_place_details(place_query: str) -> dict`, that:
   - Calls Text Search (or Find Place) with the query.
   - Takes the first result’s `place_id`, then calls Place Details.
   - Returns a normalized dict: `name`, `latitude`, `longitude`, `rating`, `user_ratings_total`, `reviews` (list of text or summary), `types`, `address`, etc.
3. Add **error handling**: no results, missing fields, API errors (catch and log, return partial or None).
4. Add **rate limiting**: e.g. `time.sleep(0.5)` or use `tenacity` between calls to avoid quota errors.
5. Optional: use **Geocoding API** as fallback when Places returns no coordinates (e.g. address-only input).

**Validation:** Script that runs `fetch_place_details("Statue of Liberty")` and prints coordinates, rating, and review count.

---

### Step 4: Enrich all places (batch)

**File:** `src/main.py` (or a dedicated `src/enrich_places.py`)

**Tasks:**

1. Call `load_places(input_path)` to get the list of places.
2. For each place, call `fetch_place_details(place_name_or_address)`.
3. Collect results into a list of enriched dicts; keep track of failures (log or store in a separate list).
4. Optionally save an intermediate JSON/CSV of enriched data for debugging.

**Validation:** Run on 2–3 places and confirm CSV/JSON has lat, lng, reviews count, and details.

---

### Step 5: LLM categorization

**File:** `src/categorize.py`

**Tasks:**

1. Define the four categories: **Restaurants**, **Street food**, **Shopping**, **Attractions**.
2. Build a prompt that includes:
   - Place `name`, `types` (from Google), and optionally a short snippet of `reviews` or `rating`/`user_ratings_total`.
   - Instruction to assign exactly one category and to respond in a fixed format (e.g. one word or a single line).
3. Use **OpenAI** or **Anthropic** SDK:
   - Call the API with the prompt, parse the response to get a single category string.
   - Normalize to one of the four (handle typos/synonyms: e.g. "restaurant" → "Restaurants").
4. Implement **batch or single-place** calls; if batching, ensure output order matches input order.
5. Add retries and error handling; on failure, assign a default category (e.g. "Attractions") and log.

**Validation:** Unit test with a few mock place dicts; check that output is always one of the four categories.

---

### Step 6: Map category to icon color

**Tasks:**

1. In `config/settings.py` or `src/export.py`, define a mapping, e.g.:
   - Restaurants → red  
   - Street food → orange  
   - Shopping → blue  
   - Attractions → green  
2. Use this when building the final CSV so each row has an `Icon_Color` column.

---

### Step 7: Master store and export CSV for Google My Maps

**File:** `src/export.py` (and optionally `src/store.py` or logic in export)

**Tasks:**

1. **Master store:** Keep a single source of truth (e.g. `data/master_places.csv` or SQLite) with columns: Name, Latitude, Longitude, Category, Icon_Color, and optionally address, rating, place_id. New results (from bulk or single-place run) are **merged into** this store (no duplicates by place_id or name+address).
2. **Regenerate CSV:** The export step reads **all** places from the master store and writes one CSV: **Name, Latitude, Longitude, Category, Icon_Color**.
3. Save to `data/output/mymaps_export_YYYYMMDD_HHMM.csv` (or a fixed name like `mymaps_export.csv` so you always re-import the same filename).
4. Use UTF-8. After each pipeline run (bulk or single place), this CSV is regenerated so you can re-import it into My Maps whenever you want an updated map.

**Validation:** Open the CSV in a text editor and in My Maps via Import; confirm columns map correctly and pins appear.

---

### Step 8: End-to-end pipeline and CLI

**File:** `src/main.py` and `scripts/run_agent.py`

**Tasks:**

1. `main.py`: Orchestrate:
   - Load places → Enrich via Google Places → Categorize with LLM → Map to icon color → **Merge into master store** → **Regenerate CSV** (from full store).
2. `scripts/run_agent.py`: Parse CLI (e.g. path to input CSV/txt, optional output path), call `main.run(...)`.
3. Log progress (e.g. “Enriched 5/10”, “Categorized 10/10”) and any errors.

**Validation:** Run from CLI with a small input file; confirm one CSV in `data/output/` and successful import in My Maps.

---

### Step 9: Error handling and robustness

**Tasks:**

1. Wrap API calls in try/except; log and continue or skip place on failure.
2. Add a simple retry for transient errors (e.g. 429, 5xx) with backoff (e.g. `tenacity`).
3. Validate CSV output: no missing lat/lng, category always one of four.

---

### Step 10: Tests and sample data

**Tasks:**

1. Add `data/input/places_sample.csv` with a few example rows (e.g. "Statue of Liberty", "Eiffel Tower", a known restaurant).
2. Unit tests: `test_load_places.py`, `test_categorize.py`, `test_export.py`; mock Google and LLM in tests.
3. Optional: one integration test with a real API key (or skip in CI).

---

## Part C: Google My Maps — regenerate CSV then manual re-import

1. After every run (bulk or single place), the pipeline **regenerates** the CSV in `data/output/` from the **master store**.
2. Open [Google My Maps](https://www.google.com/maps/d/). **First time:** Create new map → **Import** → upload that CSV → map columns (Name, Latitude, Longitude, Category, Icon_Color) → style by Category.
3. **Later:** When you add more places and want the map updated, open the same map → **Import** again (or add layer) with the **new** CSV from `data/output/`. So the workflow is: run pipeline → regenerate CSV → manually re-import the file into My Maps.

---

## Dependency Summary

| Step | Depends on |
|------|------------|
| 1. Config | — |
| 2. Load places | Config (paths) |
| 3. Google Places | Config (API key) |
| 4. Enrich batch | Load places, Google Places |
| 5. Categorize | Config (LLM key) |
| 6. Icon color | — |
| 7. Export | Categorize, icon mapping |
| 8. Pipeline + CLI | All above |
| 9. Error handling | Steps 3–8 |
| 10. Tests | All modules |

Following this order keeps the project incremental and testable at each stage.
