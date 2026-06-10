import logging
import asyncio
import discord

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:

    def __init__(self):
        # =====================================================
        # UI LOCKS (prevents race conditions per guild)
        # =====================================================
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # MAIN UPDATE ENTRY
    # =====================================================
    async def update(self, guild: discord.Guild):

        lock = self._get_lock(guild.id)

        async with lock:
            await self._update_locked(guild)

    # =====================================================
    # INTERNAL SAFE UPDATE (NO RACES)
    # =====================================================
    async def _update_locked(self, guild: discord.Guild):

        state = music_manager.get_player(guild.id)

        # -------------------------------------------------
        # SAFETY: must have channel
        # -------------------------------------------------
        if not state.channel_id:
            logging.warning("[UI] ABORT no channel_id guild=%s", guild.id)
            return

        channel = guild.get_channel(state.channel_id)

        if not channel:
            logging.warning("[UI] ABORT missing channel guild=%s", guild.id)
            return

        embed = build_now_playing_embed(state)
        view = MusicPlayerView()

        # -------------------------------------------------
        # FETCH EXISTING MESSAGE
        # -------------------------------------------------
        message = None

        if state.message_id:
            try:
                message = await channel.fetch_message(state.message_id)
            except discord.NotFound:
                state.message_id = None
                message = None
            except Exception:
                logging.exception("[UI] fetch failed")
                return

        # -------------------------------------------------
        # CREATE OR UPDATE
        # -------------------------------------------------
        if message is None:

            try:
                msg = await channel.send(
                    embed=embed,
                    view=view
                )

                state.message_id = msg.id
                state.channel_id = channel.id

                logging.info("[UI] created message=%s", msg.id)

            except Exception:
                logging.exception("[UI] failed to create message")
                return

        else:

            try:
                await message.edit(
                    embed=embed,
                    view=view
                )

                logging.info("[UI] updated message=%s", message.id)

            except Exception:
                logging.exception("[UI] failed to update message")


player_message_manager = PlayerMessageManager()