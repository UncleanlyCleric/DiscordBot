import json
import os
import asyncio
import tempfile

# -----------------------------------------------------
# PATH SETUP (always stable, relative to project root)
# -----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_PATH = os.path.join(BASE_DIR, "quotes.json")

_lock = asyncio.Lock()


# -----------------------------------------------------
# FILE BOOTSTRAP (auto-create if missing or broken)
# -----------------------------------------------------
def _ensure_file():
    os.makedirs(BASE_DIR, exist_ok=True)

    if not os.path.exists(FILE_PATH):
        _write({})
        return

    # If file exists but is invalid JSON → reset it
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception:
        _write({})


# -----------------------------------------------------
# READ
# -----------------------------------------------------
def _read():
    _ensure_file()

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


# -----------------------------------------------------
# ATOMIC WRITE
# -----------------------------------------------------
def _write(data):
    dir_name = os.path.dirname(FILE_PATH)

    fd, temp_path = tempfile.mkstemp(
        dir=dir_name,
        prefix="quotes_",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=4, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())

        os.replace(temp_path, FILE_PATH)

    except Exception:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise


# -----------------------------------------------------
# INIT (called on bot startup)
# -----------------------------------------------------
async def init():
    _ensure_file()


# -----------------------------------------------------
# ADD QUOTE
# -----------------------------------------------------
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


# -----------------------------------------------------
# RANDOM QUOTE
# -----------------------------------------------------
async def fetch_random(guild_id: int, category: str):
    import random

    data = _read()
    guild = data.get(str(guild_id), {})
    cat = guild.get(category.lower(), [])

    if not cat:
        return None

    return random.choice(cat)["content"]


# -----------------------------------------------------
# SEARCH
# -----------------------------------------------------
async def search(guild_id: int, query: str):
    data = _read()
    guild = data.get(str(guild_id), {})

    results = []

    for category, quotes in guild.items():
        for q in quotes:
            if query.lower() in q["content"].lower():
                results.append((q["id"], category, q["content"]))

    return results


# -----------------------------------------------------
# DELETE
# -----------------------------------------------------
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


# -----------------------------------------------------
# EDIT
# -----------------------------------------------------
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