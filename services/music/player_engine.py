import time
import asyncio
import logging

import wavelink
from services.music.manager import music_manager


class MusicEngine:

    def __init__(self):
        self._ui_tasks = {}

    # =====================================================
    # ENQUEUE
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
    # START
    # =====================================================
    async def start(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        if state.current:
            logging.info("[MUSIC] start() ignored, already playing")
            return

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        next_track = state.queue.next()

        logging.info(
            "[MUSIC] play_next guild=%s queue_size=%s",
            player.guild.id,
            len(state.queue.all())
        )

        # =====================================================
        # END STATE
        # =====================================================
        if not next_track:

            logging.info("[MUSIC] Queue empty guild=%s", player.guild.id)

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._update_ui(player)
            return

        # =====================================================
        # SET CURRENT
        # =====================================================
        state.current = next_track
        state.current_started_at = time.time()

        duration = getattr(getattr(next_track, "playable", None), "length", None)
        state.current_duration = duration

        logging.info(
            "[MUSIC] Now playing=%s duration=%s",
            next_track.title,
            duration
        )

        # =====================================================
        # PLAY
        # =====================================================
        try:
            await player.play(next_track.playable)

        except Exception:
            logging.exception("[MUSIC] Failed playing %s", next_track.title)

            state.current = None
            await self._play_next(player)
            return

        # =====================================================
        # UI (ONLY ON TRACK CHANGE — NOT LOOP)
        # =====================================================
        await self._update_ui(player)

        self._start_ui_loop(player)

    # =====================================================
    # SKIP (FIXED)
    # =====================================================
    async def skip(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.info("[MUSIC] skip() guild=%s", player.guild.id)

        # IMPORTANT: do NOT pre-manipulate queue state here
        # let _play_next handle correctness

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
        except Exception:
            pass

        # ONLY ONE SOURCE OF TRUTH
        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.info("[MUSIC] stop() guild=%s", player.guild.id)

        state.queue.clear()

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
        except Exception:
            pass

        try:
            await player.disconnect()
        except Exception:
            pass

        await self._update_ui(player)

        # stop UI loop cleanly
        task = self._ui_tasks.pop(player.guild.id, None)
        if task:
            task.cancel()

    # =====================================================
    # UI UPDATE (SINGLE SOURCE OF TRUTH)
    # =====================================================
    async def _update_ui(self, player):

        try:
            from services.music.player_message_manager import player_message_manager
            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception("[MUSIC] UI update failed")

    # =====================================================
    # UI LOOP (FIXED: NO DUPLICATE SPAM)
    # =====================================================
    def _start_ui_loop(self, player):

        guild_id = player.guild.id

        existing = self._ui_tasks.get(guild_id)
        if existing:
            existing.cancel()

        self._ui_tasks[guild_id] = asyncio.create_task(self._ui_tick(player))

    async def _ui_tick(self, player):

        try:
            while True:

                state = music_manager.get_player(player.guild.id)

                # stop loop if nothing playing
                if not state.current:
                    return

                await self._update_ui(player)

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            return


engine = MusicEngine()