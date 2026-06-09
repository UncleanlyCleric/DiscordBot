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
        "[MUSIC] Queued '%s' for guild %s",
        getattr(track, "title", "Unknown"),
        player.guild.id
    )

    # =====================================================
    # START PLAYBACK IF IDLE
    # =====================================================
    async def start(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        if state.current:
            return

        await self._play_next(player)

    # =====================================================
    # PLAY NEXT TRACK
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        next_track = state.queue.next()

        if not next_track:

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

        try:
            await player.play(next_track.playable)

            logging.info(
                "[MUSIC] Playing '%s' in guild %s",
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

        except Exception:
            logging.exception(
                "[MUSIC] Failed UI update after play"
            )

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

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
            from services.music.player_message_manager import (
                player_message_manager
            )

            await player_message_manager.update(player.guild)

        except Exception:
            logging.exception(
                "[MUSIC] Failed UI update after stop"
            )


engine = MusicEngine()
