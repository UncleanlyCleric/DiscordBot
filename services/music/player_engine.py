# services/music/player_engine.py

import time
import asyncio
import logging

import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:

    def __init__(self):
        self._ui_tasks = {}
        self._ui_running = set()
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

            logging.info(
                "[MUSIC] start() ignored current=%s",
                state.current.title
            )
            return


        await self._play_next(player)

    # =====================================================
    # PLAY NEXT
    # =====================================================

    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        next_track = state.queue.next()

        logging.info(
            "[PLAY_NEXT] queue_before=%s",
            len(state.queue.all())
)

        logging.info(
            "[PLAY_NEXT] selected=%s queue_remaining=%s history=%s",
            getattr(next_track, "title", None),
            len(state.queue.all()),
            len(getattr(state, "history", []))
        )

        if not next_track:

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._update_ui(player)
            return
        
        logging.info(
            "[PLAY_NEXT] playing=%s queue_after=%s",
            next_track.title,
            len(state.queue.all())
        )

        # =====================================================
        # HISTORY
        # =====================================================

        if not hasattr(state, "history"):
            state.history = []

        state.current = next_track
        state.last_track = next_track

        # only add if not duplicate
        if (
            not state.history
            or state.history[-1].uri != next_track.uri
        ):
            state.history.append(next_track)

        # keep history from growing forever
        state.history = state.history[-50:]

        state.current_started_at = time.time()

        duration = getattr(
            getattr(next_track, "playable", None),
            "length",
            None
        )

        state.current_duration = duration

        try:
            await player.play(next_track.playable)

        except Exception:
            logging.exception(
                "[PLAY_NEXT] failed playing %s",
                next_track.title
            )

            state.current = None
            await self._play_next(player)
            return

        await self._update_ui(player)

        # UI loop guard (prevents restart spam)
        if player.guild.id not in self._ui_running:
            self._start_ui_loop(player)

    # =====================================================
    # TRACK END
    # =====================================================

    async def handle_track_end(self, player: wavelink.Player):

        logging.info(
              "[TRACK_END] manual_skip=%s",
            guild_id in self._manual_skip
        )

        guild_id = player.guild.id

        start = music_manager.get_player(guild_id)
        finished_track = start.current

        if guild_id in self._manual_skip:

            self._manual_skip.remove(guild_id)

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._play_next(player)
            return

        # ==========================================
        # TRACK LOOP
        # ==========================================

        if state.loop_track and finished_track:

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            try:
                state.queue._queue.appendleft(finished_track)
            except Exception:
                state.queue.add(finished_track)

            await asyncio.sleep(0.25)
            await self._play_next(player)
            return

        # ==========================================
        # QUEUE LOOP
        # ==========================================

        if state.loop_queue and finished_track:
            state.queue.add(finished_track)

        # ==========================================
        # NORMAL FLOW
        # ==========================================

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await asyncio.sleep(0.25)
        await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================

    async def skip(self, player):

        guild_id = player.guild.id

        self._manual_skip.add(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

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

        state.loop_track = False
        state.loop_queue = False

        # DELETE PLAYER MESSAGE
        try:
            if state.player_message_id:

                channel = player.guild.get_channel(state.player_channel_id)

                if channel:
                    message = await channel.fetch_message(state.player_message_id)
                    await message.delete()

        except Exception:
            pass

        state.player_message_id = None
        state.player_channel_id = None

        task = self._ui_tasks.pop(guild_id, None)

        if task:
            task.cancel()

        self._ui_running.discard(guild_id)

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
    # PREVIOUS TRACK / RESTART TRACK
    # =====================================================

    async def previous(self, player):

        state = music_manager.get_player(
            player.guild.id
        )

        elapsed = 0

        if state.current_started_at:
            elapsed = (
                time.time()
                - state.current_started_at
            )

        # -----------------------------------------
        # restart current track if >3 seconds
        # -----------------------------------------

        if elapsed > 3:

            if state.current:

                state.queue.add_front(
                    state.current
                )

                self._manual_skip.add(
                    player.guild.id
                )
                logging.info(
                    "[PREVIOUS] selected previous=%s",
                    previous_track.title
)
                try:
                    await player.stop()
                except Exception:
                    pass

            return

        # -----------------------------------------
        # previous track if <=3 seconds
        # -----------------------------------------

        history = getattr(
            state,
            "history",
            []
        )
        
        logging.info(
            "[PREVIOUS] current=%s history=%s queue=%s",
            getattr(state.current, "title", None),
            len(history),
            len(state.queue.all())
        )
        
        if len(history) < 2:
            return

        # remove current track entry
        history.pop()

        # look at previous track
        previous_track = history[-1]

        state.queue.add_front(
            previous_track
        )

        self._manual_skip.add(
            player.guild.id
        )

        try:
            await player.stop()
        except Exception:
            pass

        
    # =====================================================
    # UI UPDATE
    # =====================================================

    async def _update_ui(self, player):

        try:
            await player_message_manager.update(player.guild)
        except Exception:
            logging.exception("[MUSIC] UI update failed")

    # =====================================================
    # UI LOOP
    # =====================================================

    def _start_ui_loop(self, player):

        guild_id = player.guild.id

        old = self._ui_tasks.pop(guild_id, None)

        if old:
            old.cancel()

        logging.info("[UI_LOOP] started guild=%s", guild_id)

        self._ui_running.add(guild_id)

        self._ui_tasks[guild_id] = asyncio.create_task(
            self._ui_tick(player)
        )

    async def _ui_tick(self, player):

        guild_id = player.guild.id

        try:
            while True:

                state = music_manager.get_player(guild_id)

                if not state.current:
                    logging.info("[UI_LOOP] exiting no current track")
                    return

                await self._update_ui(player)
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logging.info("[UI_LOOP] cancelled")

        finally:
            self._ui_running.discard(guild_id)


engine = MusicEngine()