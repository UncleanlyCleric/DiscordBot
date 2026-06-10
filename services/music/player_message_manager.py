import logging
import discord

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:

    async def update(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        if not state.player_channel_id:
            logging.warning("[UI] ABORT no channel_id guild=%s", guild.id)
            return

        channel = guild.get_channel(state.player_channel_id)

        if not channel:
            logging.warning("[UI] ABORT missing channel guild=%s", guild.id)
            return

        embed = build_now_playing_embed(state)

        message = None

        # =====================================================
        # resolve existing message safely
        # =====================================================
        if state.player_message_id:
            try:
                message = await channel.fetch_message(state.player_message_id)
            except Exception:
                message = None
                state.player_message_id = None

        # =====================================================
        # create if missing
        # =====================================================
        if message is None:

            try:
                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id

                logging.info("[UI] created message=%s", msg.id)

            except Exception:
                logging.exception("[UI] failed to create message")
                return

        # =====================================================
        # update existing
        # =====================================================
        else:
            try:
                await message.edit(
                    embed=embed,
                    view=MusicPlayerView()
                )

                logging.info("[UI] updated message=%s", message.id)

            except discord.NotFound:
                state.player_message_id = None
                await self.update(guild)

            except Exception:
                logging.exception("[UI] failed to update message")


player_message_manager = PlayerMessageManager()