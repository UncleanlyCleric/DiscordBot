import discord
import logging

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed
from services.music.ui.music_player_view import MusicPlayerView


class PlayerMessageManager:
    """
    Single source of truth for now-playing UI.
    """

    async def update(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        channel_id = state.player_channel_id
        message_id = state.player_message_id

        logging.info(
            "[UI] update guild=%s channel=%s message=%s",
            guild.id,
            channel_id,
            message_id
        )

        if not channel_id:
            logging.warning("[UI] ABORT no channel_id guild=%s", guild.id)
            return

        # =====================================================
        # GET CHANNEL
        # =====================================================
        channel = guild.get_channel(channel_id)

        if channel is None:
            try:
                channel = await guild.fetch_channel(channel_id)
            except Exception as e:
                logging.error("[UI] fetch channel failed: %s", e)
                return

        embed = build_now_playing_embed(state)

        # =====================================================
        # UPDATE EXISTING MESSAGE
        # =====================================================
        if message_id:
            try:
                msg = await channel.fetch_message(message_id)

                await msg.edit(
                    embed=embed,
                    view=MusicPlayerView()
                )

                logging.info("[UI] updated message=%s", message_id)
                return

            except Exception:
                logging.warning("[UI] existing message failed, recreating")

        # =====================================================
        # CREATE ONLY ONCE
        # =====================================================
        try:
            msg = await channel.send(
                embed=embed,
                view=MusicPlayerView()
            )

            state.player_message_id = msg.id
            state.player_channel_id = channel.id

            logging.info("[UI] created message=%s", msg.id)

        except Exception as e:
            logging.error("[UI] create failed: %s", e)