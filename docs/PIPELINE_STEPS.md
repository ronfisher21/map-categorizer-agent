# Pipeline step input/output

Table of each step’s **input** and **output** files as implemented in the codebase ([config/settings.py](../config/settings.py), [src/main.py](../src/main.py), [main.py](../main.py)).

All step inputs and outputs use the **steps hierarchy**: `data/steps/input/` and `data/steps/output/`.

| Step | RUN_STEP | Input file(s) | Output file(s) |
|------|----------|---------------|----------------|
| **1 – Load** | `load` | `data/steps/input/<INPUT_FILE>` (CSV or .txt from `.env`; e.g. `יפן.csv`) | `data/steps/output/places_loaded.json` |
| **2 – Enrich** | `enrich` | **Standalone:** same as step 1 (`data/steps/input/<INPUT_FILE>`). **After step 1 (full pipeline):** `data/steps/output/places_loaded.json` | `data/steps/output/enriched.json` |
| **3 – Categorize** | `categorize` | `data/steps/output/enriched.json` | `data/steps/output/categorized.json` |
| **Full pipeline** | `all` (default) | `data/steps/input/<INPUT_FILE>` (only for step 1; steps 2 and 3 read from the step outputs above) | All three: `places_loaded.json`, `enriched.json`, `categorized.json` in `data/steps/output/` |

**Paths:** Step input dir = `data/steps/input/` (set as `INPUT_DIR`). Step output dir = `data/steps/output/` ([config/settings.py](../config/settings.py)).

**Note:** Step 2 can be run in two ways: with `input_path` set (e.g. from `main.py` when `RUN_STEP=enrich`) it reads from the CSV/txt in `data/steps/input/`; with `input_path=None` (e.g. inside `run_full_pipeline`) it reads from `data/steps/output/places_loaded.json`.

**Legacy enriched file:** If you already have an enriched JSON in `data/output/` (e.g. `enriched_YYYYMMDD_HHMM.json`), copy it to `data/steps/output/enriched.json` to run the categorize step without re-enriching:  
`cp data/output/enriched_*.json data/steps/output/enriched.json`
