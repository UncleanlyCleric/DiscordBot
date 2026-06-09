import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed
from services.music.ui.music_player_view import MusicPlayerView


class PlayerMessageManager:

    async def update(
        self,
        guild: discord.Guild,
        channel: discord.abc.Messageable
    ):
        if not guild or not channel:
            return

        state = music_manager.get_player(guild.id)

        embed = build_now_playing_embed(state)

        # =====================================================
        # CREATE
        # =====================================================
        if not state.player_message_id:

            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id

            return

        # =====================================================
        # UPDATE EXISTING
        # =====================================================
        try:

            msg = await channel.fetch_message(
                state.player_message_id
            )

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

            return

        except Exception:
            pass

        # =====================================================
        # RECREATE IF DELETED
        # =====================================================
        msg = await channel.send(
            embed=embed,
            view=MusicPlayerView()
        )

        state.player_message_id = msg.id
        state.player_channel_id = channel.id


player_message_manager = PlayerMessageManager()