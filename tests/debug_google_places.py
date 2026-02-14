from src.google_places import fetch_place_details
from src.load_places import load_places


x = load_places("data/input/יפן.csv")
result = fetch_place_details(x[0]['name'])
print(result)