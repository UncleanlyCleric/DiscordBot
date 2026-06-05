import json
import os

FILE_PATH = "quotes.json"


def load_quotes():
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_quotes(quotes):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=4, ensure_ascii=False)