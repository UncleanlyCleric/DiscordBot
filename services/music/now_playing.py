import discord


def build_now_playing_embed(state):

    embed = discord.Embed(
        title="🎵 Now Playing",
        color=discord.Color.blurple()
    )

    if state.current:

        embed.add_field(
            name="Track",
            value=state.current.title,
            inline=False
        )

        if getattr(state.current, "author", None):
            embed.add_field(
                name="Artist",
                value=state.current.author,
                inline=True
            )

        if getattr(state.current, "requester_id", None):
            embed.add_field(
                name="Requested By",
                value=f"<@{state.current.requester_id}>",
                inline=True
            )

        thumbnail = getattr(
            state.current.playable,
            "artwork",
            None
        )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

    else:

        embed.add_field(
            name="Track",
            value="Nothing currently playing",
            inline=False
        )

    queue = state.queue.all()

    embed.add_field(
        name="Queue",
        value=str(len(queue)),
        inline=True
    )

    if queue:

        preview = "\n".join(
            f"{i + 1}. {track.title}"
            for i, track in enumerate(queue[:5])
        )

        embed.add_field(
            name="Up Next",
            value=preview,
            inline=False
        )

        if len(queue) > 5:
            embed.set_footer(
                text=f"+{len(queue) - 5} more tracks queued"
            )

    return embed