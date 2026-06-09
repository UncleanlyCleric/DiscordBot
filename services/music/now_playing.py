import discord
import time

def _progress_bar(current: float, total: float, size: int = 12):
    if not total:
        return "▬" * size

    ratio = min(max(current / total, 0), 1)
    filled = int(ratio * size)

    return "▰" * filled + "▱" * (size - filled)


def build_now_playing_embed(state):

    embed = discord.Embed(
        title="🎵 Now Playing",
        color=discord.Color.blurple()
    )

    track = state.current

    if not track:
        embed.add_field(
            name="Track",
            value="Nothing playing",
            inline=False
        )
        return embed

    embed.add_field(
        name="Track",
        value=track.title,
        inline=False
    )

    if getattr(track, "author", None):
        embed.add_field(
            name="Artist",
            value=track.author,
            inline=True
        )

    # =====================================================
    # LIVE PROGRESS (🔥 NEW)
    # =====================================================
    started = getattr(state, "current_started_at", None)
    duration = getattr(track, "length", None)

    if started and duration:
        elapsed = (time.time() - started) * 1000

        bar = _progress_bar(elapsed, duration)

        embed.add_field(
            name="Progress",
            value=f"`{bar}`",
            inline=False
        )

    embed.add_field(
        name="Queue",
        value=str(len(state.queue)),
        inline=True
    )

    return embed