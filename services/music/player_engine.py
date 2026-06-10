import time
import asyncio
import logging

import wavelink
from services.music.manager import music_manager


class MusicEngine:

    def __init__(self):
        self._ui_tasks = {}

    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        state = music_manager.get_player(player.guild.id)
        state.queue.add(track)

        logging.info(
            "[MUSIC] enqueue() guild=%s track=%s queue_size=%s",
            player.guild.id,
            getattr(track, "title", "Unknown"),
            len(state.queue.all())
        )

    # =====================================================
    async def start(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        if state.current:
            return

        await self._play_next(player)

    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        next_track = state.queue.next()

        if not next_track:

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._update_ui(player)
            return

        state.current = next_track
        state.current_started_at = time.time()
        state.current_duration = getattr(
            getattr(next_track, "playable", None),
            "length",
            None
        )

        try:
            await player.play(next_track.playable)

        except Exception:
            logging.exception("[MUSIC] play failed %s", next_track.title)

            state.current = None
            await self._play_next(player)
            return

        await self._update_ui(player)
        self._start_ui_loop(player)

    # =====================================================
    async def skip(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.info("[MUSIC] skip() guild=%s", player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
        except Exception:
            pass

        # IMPORTANT: ONLY ONE PATH
        await self._play_next(player)

    # =====================================================
    async def stop(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        state.queue.clear()

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
            await player.disconnect()
        except Exception:
            pass

        await self._update_ui(player)

        task = self._ui_tasks.pop(player.guild.id, None)
        if task:
            task.cancel()

    # =====================================================
    async def _update_ui(self, player):

        try:
            from services.music.player_message_manager import player_message_manager

            # IMPORTANT: SINGLE UPDATE ONLY
            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception("[MUSIC] UI update failed")

    # =====================================================
    def _start_ui_loop(self, player):

        guild_id = player.guild.id

        task = self._ui_tasks.get(guild_id)
        if task:
            task.cancel()

        self._ui_tasks[guild_id] = asyncio.create_task(
            self._ui_tick(player)
        )

    async def _ui_tick(self, player):

        try:
            while True:

                state = music_manager.get_player(player.guild.id)

                if not state.current:
                    return

                await self._update_ui(player)

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            return


engine = MusicEngine()