import time
import asyncio
import logging

import wavelink

from services.music.manager import music_manager


class MusicEngine:

    def __init__(self):
        # guild_id -> task
        self._ui_tasks = {}

    # =====================================================
    # UI SCHEDULER (OPTION B CORE)
    # =====================================================
    async def _start_ui_loop(self, player: wavelink.Player):
        guild_id = player.guild.id

        if guild_id in self._ui_tasks:
            return

        async def loop():
            from services.music.player_message_manager import player_message_manager

            while True:
                state = music_manager.get_player(guild_id)

                if not state.current:
                    break

                try:
                    await player_message_manager.update(player.guild)
                except Exception:
                    logging.exception("[MUSIC] UI loop update failed")

                await asyncio.sleep(5)

            self._ui_tasks.pop(guild_id, None)

        self._ui_tasks[guild_id] = asyncio.create_task(loop())

    async def _stop_ui_loop(self, guild_id: int):
        task = self._ui_tasks.pop(guild_id, None)
        if task:
            task.cancel()

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
    # NEXT TRACK
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        next_track = state.queue.next()

        if not next_track:

            state.current = None
            state.current_started_at = None
            state.current_duration = None

            await self._stop_ui_loop(player.guild.id)

            from services.music.player_message_manager import player_message_manager
            await player_message_manager.update(player.guild)

            return

        state.current = next_track
        state.current_started_at = time.time()
        state.current_duration = getattr(next_track.playable, "length", None)

        try:
            await player.play(next_track.playable)

            logging.info(
                "[MUSIC] Playing '%s' guild=%s",
                next_track.title,
                player.guild.id
            )

            # 🔥 START LIVE UI LOOP HERE
            await self._start_ui_loop(player)

        except Exception:
            logging.exception("[MUSIC] playback failed %s", next_track.title)
            state.current = None
            await self._play_next(player)
            return

        from services.music.player_message_manager import player_message_manager
        await player_message_manager.update(player.guild)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        state = music_manager.get_player(player.guild.id)

        logging.info("[MUSIC] skip() guild=%s", player.guild.id)

        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await self._stop_ui_loop(player.guild.id)

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

        logging.info("[MUSIC] stop() guild=%s", player.guild.id)

        state.queue.clear()
        state.current = None
        state.current_started_at = None
        state.current_duration = None

        await self._stop_ui_loop(player.guild.id)

        try:
            await player.stop()
        except Exception:
            pass

        from services.music.player_message_manager import player_message_manager
        await player_message_manager.update(player.guild)


engine = MusicEngine()