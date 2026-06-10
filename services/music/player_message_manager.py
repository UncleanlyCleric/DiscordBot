import logging
import discord

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:

    async def update(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        # =====================================================
        # SAFETY: channel must exist
        # =====================================================
        if not state.player_channel_id:
            logging.warning("[UI] ABORT no channel_id guild=%s", guild.id)
            return

        channel = guild.get_channel(state.player_channel_id)

        if not channel:
            logging.warning("[UI] ABORT missing channel guild=%s", guild.id)
            return

        embed = build_now_playing_embed(state)

        # =====================================================
        # SINGLE MESSAGE RULE
        # =====================================================
        if state.message is None:

            try:
                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.message = msg

                logging.info("[UI] created message=%s", msg.id)

            except Exception:
                logging.exception("[UI] failed to create message")
                return

        else:

            try:
                await state.message.edit(
                    embed=embed,
                    view=MusicPlayerView()
                )

                logging.info("[UI] updated message=%s", state.message.id)

            except discord.NotFound:
                # message deleted → rebuild once
                state.message = None
                await self.update(guild)

            except Exception:
                logging.exception("[UI] failed to update message")


player_message_manager = PlayerMessageManager()