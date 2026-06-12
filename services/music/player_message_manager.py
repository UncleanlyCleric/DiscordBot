import logging
import discord

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed

class PlayerMessageManager:

    # =====================================================
    # DELETE PLAYER MESSAGE
    # =====================================================

    async def delete(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        if not state.player_channel_id:
            return

        channel = guild.get_channel(
            state.player_channel_id
        )

        if not channel:
            return

        try:

            if state.player_message_id:

                message = await channel.fetch_message(
                    state.player_message_id
                )

                await message.delete()

        except discord.NotFound:
            pass

        except Exception:
            logging.exception(
                "[UI] failed delete"
            )

        state.player_message_id = None
        state.player_channel_id = None

    # =====================================================
    # UPDATE PLAYER MESSAGE
    # =====================================================

    async def update(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        if not state.player_channel_id:
            logging.warning(
                "[UI] no player_channel_id guild=%s",
                guild.id
            )
            return

        channel = guild.get_channel(
            state.player_channel_id
        )

        if not channel:
            logging.warning(
                "[UI] channel missing guild=%s channel=%s",
                guild.id,
                state.player_channel_id
            )
            return

        embed = build_now_playing_embed(state)

        view = MusicPlayerView()

        message = None

        if state.player_message_id:

            try:

                message = await channel.fetch_message(
                    state.player_message_id
                )

            except discord.NotFound:

                logging.warning(
                    "[UI] message missing recreating"
                )

                message = None
                state.player_message_id = None

            except Exception:

                logging.exception(
                    "[UI] fetch failed"
                )
                return

        # =====================================================
        # CREATE
        # =====================================================

        if message is None:

            try:

                msg = await channel.send(
                    embed=embed,
                    view=view
                )

                state.player_message_id = msg.id

                # self-heal channel tracking
                state.player_channel_id = channel.id

            except Exception:

                logging.exception(
                    "[UI] failed create"
                )

            return

        # =====================================================
        # UPDATE
        # =====================================================

        try:

            await message.edit(
                embed=embed,
                view=view
            )

        except discord.NotFound:

            logging.warning(
                "[UI] update target missing recreating"
            )

            state.player_message_id = None

            await self.update(guild)

        except Exception:

            logging.exception(
                "[UI] failed update"
            )

    player_message_manager = PlayerMessageManager()
