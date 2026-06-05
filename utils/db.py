import json
import os
import asyncio

FILE_PATH = "quotes.json"

_lock = asyncio.Lock()


# ---------------- INTERNAL ----------------
def _ensure_file():
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)


def _read():
    _ensure_file()

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _write(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------- INIT ----------------
async def init():
    _ensure_file()


# ---------------- ADD ----------------
async def add(guild_id: int, category: str, content: str, author_id: str):
    async with _lock:
        data = _read()

        guild = data.setdefault(str(guild_id), {})
        cat = guild.setdefault(category.lower(), [])

        quote_id = sum(len(v) for v in guild.values()) + 1

        cat.append({
            "id": quote_id,
            "content": content,
            "author": author_id
        })

        _write(data)


# ---------------- RANDOM ----------------
async def fetch_random(guild_id: int, category: str):
    import random

    data = _read()
    guild = data.get(str(guild_id), {})
    cat = guild.get(category.lower(), [])

    if not cat:
        return None

    return random.choice(cat)["content"]


# ---------------- SEARCH ----------------
async def search(guild_id: int, query: str):
    data = _read()
    guild = data.get(str(guild_id), {})

    results = []

    for category, quotes in guild.items():
        for q in quotes:
            if query.lower() in q["content"].lower():
                results.append((q["id"], category, q["content"]))

    return results


# ---------------- DELETE ----------------
async def delete(quote_id: int, guild_id: int):
    async with _lock:
        data = _read()
        guild = data.get(str(guild_id), {})

        found = False

        for category in guild:
            new_list = []

            for q in guild[category]:
                if q["id"] == quote_id:
                    found = True
                    continue
                new_list.append(q)

            guild[category] = new_list

        if found:
            _write(data)

        return found


# ---------------- EDIT ----------------
async def edit(quote_id: int, guild_id: int, new_content: str):
    async with _lock:
        data = _read()
        guild = data.get(str(guild_id), {})

        found = False

        for category in guild:
            for q in guild[category]:
                if q["id"] == quote_id:
                    q["content"] = new_content
                    found = True

        if found:
            _write(data)

        return found