import time
import logging
import asyncio

import wavelink

from services.music.manager import music_manager


class MusicEngine:

    def __init__(self):
        self._lock = asyncio.Lock()

    # =====================================================
    # ENQUEUE SINGLE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        state = music_manager.get_player(player.guild.id)

        state.queue.add(track)

        logging.info(
            "[MUSIC] enqueue() guild=%s track=%s queue_size=%s",
            player.guild.id,
            getattr(track, "title", "Unknown"),
            len(state.queue.all()) if hasattr(state.queue, "all") else 0
        )

    # =====================================================
    # ENQUEUE MANY (FIX FOR PLAYLISTS)
    # =====================================================
    async def enqueue_many(self, player: wavelink.Player, tracks):

        for t in tracks:
            await self.enqueue(player, t)

    # =====================================================
    # START PLAYBACK IF IDLE
    # =====================================================
    async def start(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.info(
            "[MUSIC] start() guild=%s current=%s queue=%s",
            player.guild.id,
            getattr(state.current, "title", None),
            len(state.queue.all()) if hasattr(state.queue, "all") else 0
        )

        if state.current:
            logging.info("[MUSIC] start() ignored, already playing")
            return

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT TRACK (LOCKED FIX)
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        async with self._lock:

            state = music_manager.get_player(player.guild.id)

            next_track = state.queue.next()

            logging.info(
                "[MUSIC] Queue size before next=%s",
                len(state.queue.all()) if hasattr(state.queue, "all") else 0
            )

            if not next_track:

                logging.info("[MUSIC] Queue empty guild=%s", player.guild.id)

                state.current = None
                state.current_started_at = None
                state.current_duration = None

                from services.music.player_message_manager import player_message_manager
                await player_message_manager.update(player.guild)

                return

            state.current = next_track
            state.current_started_at = time.time()

            duration = getattr(getattr(next_track, "playable", None), "length", None)
            state.current_duration = duration

            logging.info(
                "[MUSIC] Attempting playback title=%s duration=%s",
                next_track.title,
                duration
            )

            try:
                await player.play(next_track.playable)

                logging.info(
                    "[MUSIC] Playing '%s' guild=%s",
                    next_track.title,
                    player.guild.id
                )

            except Exception:
                logging.exception("[MUSIC] Failed playback %s", next_track.title)
                state.current = None
                await self._play_next(player)
                return

            from services.music.player_message_manager import player_message_manager
            await player_message_manager.update(player.guild)

            # =====================================================
            # UI LOOP (FIX FOR PROGRESS BAR NOT MOVING)
            # =====================================================
            asyncio.create_task(self._ui_tick(player))

    # =====================================================
    # UI TICK LOOP (FIX)
    # =====================================================
    async def _ui_tick(self, player: wavelink.Player):

        while True:
            await asyncio.sleep(5)

            state = music_manager.get_player(player.guild.id)

            if not state.current:
                return

            try:
                from services.music.player_message_manager import player_message_manager
                await player_message_manager.update(player.guild)
            except Exception:
                pass

    # =====================================================
    # SKIP (FIXED SAFE)
    # =====================================================
    async def skip(self, player: wavelink.Player):

        logging.info("[MUSIC] skip() guild=%s", player.guild.id)

        state = music_manager.get_player(player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.skip(force=True)
        except Exception:
            try:
                await player.stop()
            except Exception:
                pass

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):

        logging.info("[MUSIC] stop() guild=%s", player.guild.id)

        state = music_manager.get_player(player.guild.id)

        state.queue.clear()

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()
        except Exception:
            pass

        try:
            from services.music.player_message_manager import player_message_manager
            await player_message_manager.update(player.guild)
        except Exception:
            logging.exception("[MUSIC] UI update failed after stop")

    # =====================================================
    # TRACK END HANDLER (FIX MISSING METHOD)
    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):

        logging.info("[MUSIC] handle_track_end() guild=%s", player.guild.id)

        await self._play_next(player)


engine = MusicEngine()