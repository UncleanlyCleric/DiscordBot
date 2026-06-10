import time
import asyncio
import logging

import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:

    def __init__(self):
        self._ui_tasks = {}
        self._manual_skip = set()

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
            return

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.warning(
            "[PLAY_NEXT] queue_size=%s",
            len(state.queue.all())
        )

        next_track = state.queue.next()

        if not next_track:

            logging.info(
                "[MUSIC] Queue empty guild=%s",
                player.guild.id
            )

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._update_ui(player)
            return

        state.current = next_track
        state.current_started_at = time.time()

        duration = getattr(
            getattr(next_track, "playable", None),
            "length",
            None
        )

        state.current_duration = duration

        logging.info(
            "[MUSIC] Playing '%s' guild=%s",
            next_track.title,
            player.guild.id
        )

        logging.warning(
            "[PLAY_NEXT] attempting play: %s",
            next_track.title
        )

        try:
            await player.play(next_track.playable)

        except Exception:

            logging.exception(
                "[MUSIC] Failed playing %s",
                next_track.title
            )

            state.current = None

            await self._play_next(player)
            return

        logging.warning(
            "[PLAY_NEXT] player.play completed"
        )

        await self._update_ui(player)

        # START PROGRESS LOOP
        self._start_ui_loop(player)

    # =====================================================
    # TRACK END
    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):

        guild_id = player.guild.id

        logging.warning(
            "[TRACK_END] ENTERED guild=%s",
            guild_id
        )

        if guild_id in self._manual_skip:

            logging.warning(
                "[TRACK_END] manual skip detected"
            )

            self._manual_skip.remove(guild_id)
            return

        state = music_manager.get_player(guild_id)

        logging.warning(
            "[TRACK_END] queue_size=%s current=%s",
            len(state.queue.all()),
            getattr(state.current, "title", None)
        )

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await asyncio.sleep(0.5)

        logging.warning(
            "[TRACK_END] calling _play_next()"
        )

        await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        guild_id = player.guild.id

        self._manual_skip.add(guild_id)

        state = music_manager.get_player(guild_id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
        except Exception:
            pass

        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):

        guild_id = player.guild.id

        state = music_manager.get_player(guild_id)

        state.queue.clear()

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        task = self._ui_tasks.pop(guild_id, None)

        if task:
            task.cancel()

        try:
            await player.stop()
        except Exception:
            pass

        try:
            await player.disconnect()
        except Exception:
            pass

        await self._update_ui(player)

    # =====================================================
    # UI UPDATE
    # =====================================================
    async def _update_ui(self, player):

        try:
            await player_message_manager.update(player.guild)
        except Exception:
            logging.exception(
                "[MUSIC] UI update failed"
            )

    # =====================================================
    # UI LOOP
    # =====================================================
    def _start_ui_loop(self, player):

        guild_id = player.guild.id

        old = self._ui_tasks.pop(guild_id, None)

        if old:
            old.cancel()

        self._ui_tasks[guild_id] = asyncio.create_task(
            self._ui_tick(player)
        )

    async def _ui_tick(self, player):

        try:

            while True:

                state = music_manager.get_player(
                    player.guild.id
                )

                if not state.current:
                    return

                logging.info(
                    "[UI_LOOP] current=%s position=%s paused=%s",
                    state.current.title,
                    getattr(player, "position", None),
                    getattr(player, "paused", None)
                )

                await self._update_ui(player)

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            pass


engine = MusicEngine()