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
    else:
        embed.add_field(
            name="Track",
            value="Nothing currently playing",
            inline=False
        )

    embed.add_field(
        name="Queue",
        value=str(len(state.queue)),
        inline=True
    )

    return embed