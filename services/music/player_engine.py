import time
import logging
import wavelink

from services.music.manager import music_manager


class MusicEngine:

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

        logging.info(
            "[MUSIC] start() guild=%s current=%s queue=%s",
            player.guild.id,
            getattr(state.current, "title", None),
            len(state.queue.all())
        )

        if state.current:
            logging.info("[MUSIC] start() ignored, already playing")
            return

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT
    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        state = music_manager.get_player(player.guild.id)

        logging.info(
            "[MUSIC] handle_track_end() guild=%s",
            player.guild.id
        )

        logging.info(
            "[MUSIC] Queue size before next=%s",
            len(state.queue.all())
        )

        next_track = state.queue.next()

        logging.info(
            "[MUSIC] Next track=%s",
            getattr(next_track, "title", None)
        )

        if not next_track:
            logging.info("[MUSIC] Queue empty guild=%s", player.guild.id)

            state.current = None
            state.current_started_at = None
            state.current_duration = None

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

        except Exception:
            logging.exception("[MUSIC] playback failed %s", next_track.title)
            state.current = None
            await self._play_next(player)
            return

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await player.stop()  # IMPORTANT: forces track_end event

        # let handle_track_end() drive next track

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

    # =====================================================
    # Desync Fix
    # =====================================================
    # This function is called when a track ends, and it's used to fix desynchronization issues.
    async def handle_track_end(self, player: wavelink.Player):
        import logging

        logging.info(
            "[MUSIC] handle_track_end() guild=%s",
            getattr(player.guild, "id", None)
        )

        state = music_manager.get_player(player.guild.id)

        # reset current
        state.current = None
        state.current_started_at = None
        state.current_duration = None

        # IMPORTANT: continue queue
        await self._play_next(player)

engine = MusicEngine()