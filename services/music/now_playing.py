import discord
import time
import re


def _format_time(ms):

    if not ms:
        return "0:00"

    total_seconds = int(ms / 1000)

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes}:{seconds:02d}"


def _progress_bar(current, total, size=16):

    if not total:
        return "▬" * size

    ratio = min(
        max(current / total, 0),
        1
    )

    filled = int(ratio * size)

    return (
        "▰" * filled
        + "▱" * (size - filled)
    )


def _youtube_thumbnail(uri):

    if not uri:
        return None

    match = re.search(
        r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        uri
    )

    if not match:
        return None

    video_id = match.group(1)

    return (
        f"https://img.youtube.com/vi/"
        f"{video_id}/hqdefault.jpg"
    )


def build_now_playing_embed(state):

    embed = discord.Embed(
        title="🎵 Now Playing",
        color=discord.Color.blurple()
    )

    track = state.current

    if not track:

        embed.description = "Nothing playing."

        return embed

    playable = getattr(
        track,
        "playable",
        None
    )

    # =====================================================
    # ALBUM ART
    # =====================================================

    artwork = None

    if playable:

        artwork = (
            getattr(playable, "artwork", None)
            or getattr(playable, "artwork_url", None)
            or getattr(playable, "thumbnail", None)
        )

    # YouTube fallback
    if not artwork:

        artwork = _youtube_thumbnail(
            getattr(track, "uri", None)
        )

    if artwork:

        try:

            embed.set_thumbnail(
                url=str(artwork)
            )

        except Exception:
            pass

    # =====================================================
    # TRACK
    # =====================================================

    embed.add_field(
        name="Track",
        value=f"**{track.title}**",
        inline=False
    )

    if getattr(track, "author", None):

        embed.add_field(
            name="Artist",
            value=track.author,
            inline=True
        )

    # =====================================================
    # REQUESTER
    # =====================================================

    if getattr(track, "requester_id", None):

        embed.add_field(
            name="Requested By",
            value=f"<@{track.requester_id}>",
            inline=True
        )

    # =====================================================
    # PROGRESS
    # =====================================================

    started = getattr(
        state,
        "current_started_at",
        None
    )

    duration = getattr(
        state,
        "current_duration",
        None
    )

    elapsed = 0

    if started and duration:

        try:

            elapsed = (
                time.time() - started
            ) * 1000

            elapsed = max(
                0,
                min(elapsed, duration)
            )

        except Exception:

            elapsed = 0

    bar = _progress_bar(
        elapsed,
        duration
    )

    embed.add_field(
        name="Progress",
        value=(
            f"`{bar}`\n"
            f"{_format_time(elapsed)}"
            f" / "
            f"{_format_time(duration)}"
        ),
        inline=False
    )

    # =====================================================
    # PLAYBACK INFO
    # =====================================================

    queue = state.queue.all()

    next_track = (
        queue[0].title
        if queue
        else "None"
    )

    embed.add_field(
        name="Playback",
        value=(
            f"🔊 Volume: {state.volume}%\n"
            f"📜 Queue: {len(queue)} tracks\n"
            f"⏭ Next: {next_track}"
        ),
        inline=False
    )

    # =====================================================
    # LOOP STATUS
    # =====================================================

    embed.add_field(
        name="Loop",
        value=(
            f"🔂 Track: {'On' if state.loop_track else 'Off'}\n"
            f"🔁 Queue: {'On' if state.loop_queue else 'Off'}"
        ),
        inline=False
    )

    # =====================================================
    # FOOTER
    # =====================================================

    embed.set_footer(
        text="Music Player"
    )

    return embed