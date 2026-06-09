import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed
from services.music.ui.music_player_view import MusicPlayerView


class PlayerMessageManager:
    """
    Single source of truth for now-playing UI.

    Rules:
    - ONLY this class edits messages
    - Engine / cog NEVER call channel.send/edit directly
    - Always safe re-create if message is gone
    """

    async def update(self, guild: discord.Guild):
        state = music_manager.get_player(guild.id)

        channel_id = state.player_channel_id
        message_id = state.player_message_id

        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        embed = build_now_playing_embed(state)

        # =====================================================
        # FIRST TIME MESSAGE
        # =====================================================
        if not message_id:
            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id
            return

        # =====================================================
        # UPDATE EXISTING MESSAGE
        # =====================================================
        try:
            msg = await channel.fetch_message(message_id)

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

        except Exception:
            # fallback: recreate message if deleted
            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id


player_message_manager = PlayerMessageManager()