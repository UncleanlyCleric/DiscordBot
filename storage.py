import json
import os

QUOTES_FILE = "quotes.json"


def load_quotes():
    """Load quotes from JSON file"""
    if not os.path.exists(QUOTES_FILE):
        with open(QUOTES_FILE, "w") as f:
            json.dump([], f)

    with open(QUOTES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_quotes(quotes):
    """Save quotes to JSON file"""
    with open(QUOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=4, ensure_ascii=False)