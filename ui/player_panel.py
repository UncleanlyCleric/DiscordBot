import discord


class PlayerPanel:
    """
    SAFE EMBED BUILDER

    RULES:
    - NO discord state logic
    - NO music imports
    - NO side effects
    """

    def build_now_playing(self, track: dict):
        embed = discord.Embed(
            title="Now Playing",
            description=track.get("title", "Unknown"),
            color=discord.Color.blurple()
        )

        url = track.get("url")

        if url:
            embed.add_field(name="Source", value=url, inline=False)

        return embed

    def build_queue(self, queue: list):
        embed = discord.Embed(
            title="Queue",
            color=discord.Color.green()
        )

        if not queue:
            embed.description = "Empty"
            return embed

        desc = "\n".join(
            f"{i+1}. {t.get('title', 'Unknown')}"
            for i, t in enumerate(queue)
        )

        embed.description = desc

        return embed