import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:

    async def update(self, guild: discord.Guild):
        state = music_manager.get_player(guild.id)

        if not state.player_channel_id:
            return

        channel = guild.get_channel(state.player_channel_id)
        if not channel:
            return

        embed = build_now_playing_embed(state)

        from services.music.ui.music_player_view import MusicPlayerView

        # CREATE
        if not state.player_message_id:
            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id
            return

        # UPDATE
        try:
            msg = await channel.fetch_message(state.player_message_id)

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

        except Exception:
            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id


player_message_manager = PlayerMessageManager()