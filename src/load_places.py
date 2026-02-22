import csv
from pathlib import Path
import json

def load_places(input_path: str | Path) -> list[dict]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    if path.suffix.lower() == ".txt":
        return _load_txt(path)
    return _load_csv(path)


def load_enriched(input_path: str | Path) -> list[dict]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_txt(path: Path) -> list[dict]:
    places = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:
                places.append({"name": name})
    return places


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return []

    header = list(rows[0].keys())
    name_col = next((h for h in header if h.strip().lower() in ("name", "place", "title")), header[0])
    addr_col = next((h for h in header if h.strip().lower() == "address"), None)

    places = []
    for row in rows:
        name = (row.get(name_col) or "").strip()
        if not name:
            continue
        item = {"name": name}
        if addr_col and row.get(addr_col):
            item["address"] = row[addr_col].strip()
        places.append(item)
    return places
