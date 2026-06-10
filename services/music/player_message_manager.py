import logging
import discord

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
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

        message = None

        if state.player_message_id:

            try:
                message = await channel.fetch_message(
                    state.player_message_id
                )

            # ONLY recreate if message is actually gone
            except discord.NotFound:
                message = None
                state.player_message_id = None

            # Anything else should NOT create a duplicate
            except Exception:
                logging.exception(
                    "[UI] fetch failed"
                )
                return

        # =====================================================
        # CREATE MESSAGE
        # =====================================================
        if message is None:

            try:
                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id

                logging.info(
                    "[UI] created message=%s",
                    msg.id
                )

            except Exception:
                logging.exception(
                    "[UI] failed create"
                )
                return

        # =====================================================
        # UPDATE MESSAGE
        # =====================================================
        else:

            try:
                await message.edit(
                    embed=embed,
                    view=MusicPlayerView()
                )

                logging.info(
                    "[UI] updated message=%s",
                    message.id
                )

            except discord.NotFound:

                state.player_message_id = None

                await self.update(guild)

            except Exception:
                logging.exception(
                    "[UI] failed update"
                )


player_message_manager = PlayerMessageManager()