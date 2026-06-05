import json
import os
import random
from typing import List, Optional, Tuple

FILE_PATH = "quotes.json"


# ---------------- INTERNAL HELPERS ----------------
def _load():
    if not os.path.exists(FILE_PATH):
        return {}

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _save(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------- INIT ----------------
async def init():
    if not os.path.exists(FILE_PATH):
        _save({})


# ---------------- ADD ----------------
async def add(guild_id: int, category: str, content: str, author_id: str):
    data = _load()

    guild = data.setdefault(str(guild_id), {})
    cat = guild.setdefault(category.lower(), [])

    quote_id = sum(len(v) for v in guild.values()) + 1

    cat.append({
        "id": quote_id,
        "content": content,
        "author": author_id
    })

    _save(data)


# ---------------- FETCH RANDOM ----------------
async def fetch_random(guild_id: int, category: str) -> Optional[str]:
    data = _load()

    guild = data.get(str(guild_id), {})
    cat = guild.get(category.lower(), [])

    if not cat:
        return None

    q = random.choice(cat)
    return q["content"]


# ---------------- SEARCH ----------------
async def search(guild_id: int, query: str) -> List[Tuple[int, str, str]]:
    data = _load()

    guild = data.get(str(guild_id), {})

    results = []

    for category, quotes in guild.items():
        for q in quotes:
            if query.lower() in q["content"].lower():
                results.append((q["id"], category, q["content"]))

    return results


# ---------------- DELETE ----------------
async def delete(quote_id: int, guild_id: int) -> bool:
    data = _load()

    guild = data.get(str(guild_id), {})

    found = False

    for category in list(guild.keys()):
        new_list = []

        for q in guild[category]:
            if q["id"] == quote_id:
                found = True
                continue
            new_list.append(q)

        guild[category] = new_list

    if found:
        _save(data)

    return found


# ---------------- EDIT ----------------
async def edit(quote_id: int, guild_id: int, new_content: str) -> bool:
    data = _load()

    guild = data.get(str(guild_id), {})

    found = False

    for category in guild:
        for q in guild[category]:
            if q["id"] == quote_id:
                q["content"] = new_content
                found = True

    if found:
        _save(data)

    return found