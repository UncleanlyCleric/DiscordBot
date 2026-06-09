import time
import logging

import wavelink

from services.music.manager import music_manager

class MusicEngine:

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        logging.info(
            "[MUSIC] enqueue() guild=%s track=%s",
            player.guild.id,
            getattr(track, "title", "Unknown")
        )

        state = music_manager.get_player(player.guild.id)

        state.queue.add(track)

        logging.info(
            "[MUSIC] Queue size now=%s",
            len(state.queue.all())
        )

    # =====================================================
    # START PLAYBACK IF IDLE
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
            logging.info(
                "[MUSIC] start() ignored, already playing"
            )
            return

        await self._play_next(player)

    # =====================================================
    # TRACK END ENTRY POINT
    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):

        logging.info(
            "[MUSIC] handle_track_end() guild=%s",
            player.guild.id
        )

        state = music_manager.get_player(player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT TRACK
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

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

            logging.info(
                "[MUSIC] Queue empty guild=%s",
                player.guild.id
            )

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            try:
                from services.music.player_message_manager import (
                    player_message_manager
                )

                await player_message_manager.update(player.guild)

            except Exception:
                logging.exception(
                    "[MUSIC] Failed UI update after queue empty"
                )

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
            "[MUSIC] Attempting playback title=%s duration=%s",
            next_track.title,
            duration
        )

        try:

            playable = getattr(next_track, "playable", None)

            if playable is None:
                raise RuntimeError(
                    f"Track {next_track.title} missing playable"
                )

            await player.play(playable)

            logging.info(
                "[MUSIC] Playing '%s' guild=%s",
                next_track.title,
                player.guild.id
            )

        except Exception:

            logging.exception(
                "[MUSIC] Failed playing '%s'",
                next_track.title
            )

            state.current = None

            await self._play_next(player)
            return

        try:
            from services.music.player_message_manager import (
                player_message_manager
            )

            await player_message_manager.update(player.guild)

            logging.info(
                "[MUSIC] UI updated after play"
            )

        except Exception:
            logging.exception(
                "[MUSIC] Failed UI update after play"
            )

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        logging.info(
            "[MUSIC] skip() guild=%s",
            player.guild.id
        )

        state = music_manager.get_player(player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.skip(force=True)

        except Exception:

            logging.exception(
                "[MUSIC] player.skip failed, falling back to stop"
            )

            try:
                await player.stop()
            except Exception:
                logging.exception(
                    "[MUSIC] fallback stop failed"
                )

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):

        logging.info(
            "[MUSIC] stop() guild=%s",
            player.guild.id
        )

        state = music_manager.get_player(player.guild.id)

        state.queue.clear()

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        try:
            await player.stop()

        except Exception:
            logging.exception(
                "[MUSIC] player.stop failed"
            )

        try:
            from services.music.player_message_manager import (
                player_message_manager
            )

            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception(
                "[MUSIC] Failed UI update after stop"
            )

engine = MusicEngine()
