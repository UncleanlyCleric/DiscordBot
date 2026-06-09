import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:
    """
    Single source of truth for now-playing UI.
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

        # lazy import prevents circular dependency
        from services.music.ui.music_player_view import MusicPlayerView

        # =====================================================
        # CREATE UI IF IT DOES NOT EXIST
        # =====================================================
        if not message_id:
            try:
                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

            except Exception:
                pass

            return

        # =====================================================
        # UPDATE UI IF EXISTS
        # =====================================================
        try:
            msg = await channel.fetch_message(message_id)

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

        except Exception:
            # fallback: recreate UI if message lost
            try:
                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

            except Exception:
                pass


player_message_manager = PlayerMessageManager()