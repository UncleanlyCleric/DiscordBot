import aiohttp

async def get_apple_track(query: str):
    url = f"https://itunes.apple.com/search?term={query}&limit=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    return data["results"][0] if data["results"] else None