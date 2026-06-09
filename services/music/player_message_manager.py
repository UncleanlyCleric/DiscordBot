import logging

import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed

logging.info("[UI] PlayerMessageManager module loaded")


class PlayerMessageManager:
    """
    Single source of truth for now-playing UI.
    """

    async def update(self, guild: discord.Guild):

        logging.info(
            "[UI] update() CALLED guild=%s",
            getattr(guild, "id", "unknown")
        )

        state = music_manager.get_player(guild.id)

        channel_id = state.player_channel_id
        message_id = state.player_message_id

        logging.info(
            "[UI] state channel_id=%s message_id=%s current=%s",
            channel_id,
            message_id,
            getattr(state.current, "title", None)
        )

        if not channel_id:
            logging.warning(
                "[UI] ABORT: no channel_id set guild=%s",
                guild.id
            )
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            try:
                logging.info(
                    "[UI] channel not cached, fetching channel_id=%s",
                    channel_id
                )

                channel = await guild.fetch_channel(channel_id)

                logging.info(
                    "[UI] fetched channel successfully channel_id=%s",
                    channel_id
                )

            except Exception:
                logging.exception(
                    "[UI] FAILED to fetch channel_id=%s",
                    channel_id
                )
                return

        try:
            embed = build_now_playing_embed(state)

            logging.info(
                "[UI] embed built current=%s queue=%s",
                getattr(state.current, "title", None),
                len(state.queue.all())
            )

        except Exception:
            logging.exception("[UI] embed generation failed")
            return

        from services.music.ui.music_player_view import MusicPlayerView

        # =====================================================
        # FIRST MESSAGE
        # =====================================================
        if not message_id:

            try:
                logging.info(
                    "[UI] creating first player message "
                    "channel_id=%s",
                    channel.id
                )

                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

                logging.info(
                    "[UI] created player message "
                    "message_id=%s channel_id=%s",
                    msg.id,
                    channel.id
                )

            except Exception:
                logging.exception(
                    "[UI] FAILED TO CREATE PLAYER MESSAGE"
                )

            return

        # =====================================================
        # UPDATE EXISTING MESSAGE
        # =====================================================
        try:

            logging.info(
                "[UI] fetching existing message "
                "message_id=%s",
                message_id
            )

            msg = await channel.fetch_message(message_id)

            logging.info(
                "[UI] editing existing message "
                "message_id=%s",
                message_id
            )

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

            logging.info(
                "[UI] message updated successfully "
                "message_id=%s",
                message_id
            )

        except Exception:

            logging.exception(
                "[UI] UPDATE FAILED message_id=%s",
                message_id
            )

            try:

                logging.info(
                    "[UI] fallback creating new message "
                    "channel_id=%s",
                    channel.id
                )

                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

                logging.info(
                    "[UI] fallback created message "
                    "message_id=%s",
                    msg.id
                )

            except Exception:
                logging.exception(
                    "[UI] FALLBACK FAILED"
                )


player_message_manager = PlayerMessageManager()