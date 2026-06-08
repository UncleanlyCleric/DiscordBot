import asyncio
from typing import Dict

import wavelink

from services.music.manager import music_manager
from services.music.lavalink.bridge import voice_bridge
from services.music.autoplay import autoplay_engine


class MusicController:
    """
    Central playback orchestrator.

    Responsibilities:
    - consume guild queues
    - trigger Lavalink playback
    - handle autoplay fallback
    - advance tracks safely
    """

    def __init__(self):
        self.running: Dict[int, bool] = {}
        self._tasks: Dict[int, asyncio.Task] = {}

    # =====================================================
    # LOOP CONTROL
    # =====================================================

    async def start_loop(self, guild_id: int):
        """
        Start playback loop for a guild.
        Prevents duplicate loops.
        """

        if self.running.get(guild_id):
            return

        self.running[guild_id] = True

        if guild_id not in self._tasks:
            self._tasks[guild_id] = asyncio.create_task(
                self._run_loop(guild_id)
            )

    def stop_loop(self, guild_id: int):
        """
        Stop playback loop safely.
        """

        self.running[guild_id] = False

        task = self._tasks.get(guild_id)
        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    # =====================================================
    # MAIN LOOP
    # =====================================================

    async def _run_loop(self, guild_id: int):
        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                # -------------------------
                # IDLE WAIT
                # -------------------------
                if not player.is_playing:
                    await asyncio.sleep(1)
                    continue

                # -------------------------
                # GET NEXT TRACK
                # -------------------------
                track = player.current

                if not track:
                    track = player.queue.next()

                # -------------------------
                # AUTOPLAY FALLBACK
                # -------------------------
                if not track:
                    track = autoplay_engine.generate(player.current)

                    if track:
                        player.queue.add(track)
                        track = player.queue.next()

                # Still nothing to play → idle
                if not track:
                    await asyncio.sleep(2)
                    continue

                # Set current track state
                player.current = track
                player.is_playing = True

                # -------------------------
                # PLAY VIA LAVALINK
                # -------------------------
                await voice_bridge.play(guild_id, track)

                # -------------------------
                # WAIT FOR TRACK TO FINISH
                # -------------------------
                guild = next(
                    (g for g in wavelink.Pool._bot.guilds if g.id == guild_id),
                    None
                )

                if guild and guild.voice_client:
                    vc: wavelink.Player = guild.voice_client

                    # Wait until Lavalink reports idle
                    while vc.playing or vc.paused:
                        await asyncio.sleep(1)

                # -------------------------
                # ADVANCE QUEUE
                # -------------------------
                player.skip()

        except asyncio.CancelledError:
            pass

        except Exception as e:
            print(f"[MusicController] Error in guild {guild_id}: {e}")

        finally:
            self.running[guild_id] = False

    # =====================================================
    # UTILITIES
    # =====================================================

    def is_running(self, guild_id: int) -> bool:
        return self.running.get(guild_id, False)

    async def restart(self, guild_id: int):
        """
        Restart loop (useful after reconnects)
        """

        self.stop_loop(guild_id)
        await asyncio.sleep(1)
        await self.start_loop(guild_id)


music_controller = MusicController()