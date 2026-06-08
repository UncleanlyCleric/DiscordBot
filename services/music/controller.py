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
        if self.running.get(guild_id):
            return

        self.running[guild_id] = True

        if guild_id not in self._tasks:
            self._tasks[guild_id] = asyncio.create_task(
                self._run_loop(guild_id)
            )

    def stop_loop(self, guild_id: int):
        self.running[guild_id] = False

        task = self._tasks.get(guild_id)

        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    # =====================================================
    # MAIN LOOP
    # =====================================================

    async def _run_loop(self, guild_id: int):

        print(f"[MUSIC] Loop started for guild {guild_id}")

        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                print(
                    f"[MUSIC] Queue size={len(player.queue)} "
                    f"current={player.current.title if player.current else None} "
                    f"is_playing={player.is_playing}"
                )

                # -------------------------------------------------
                # If already playing something, wait.
                # -------------------------------------------------
                if player.current:
                    await asyncio.sleep(1)
                    continue

                # -------------------------------------------------
                # Get next queued track
                # -------------------------------------------------
                track = player.queue.next()

                # -------------------------------------------------
                # Autoplay fallback
                # -------------------------------------------------
                if not track:
                    track = autoplay_engine.generate(player.current)

                    if track:
                        player.queue.add(track)
                        track = player.queue.next()

                if not track:
                    await asyncio.sleep(2)
                    continue

                print(f"[MUSIC] Track selected: {track.title}")

                # -------------------------------------------------
                # Find guild
                # -------------------------------------------------
                guild = None

                for node in wavelink.Pool.nodes.values():

                    bot = getattr(node, "_client", None)

                    if bot:
                        guild = bot.get_guild(guild_id)

                    if guild:
                        break

                if not guild:
                    print("[MUSIC] Guild not found")
                    await asyncio.sleep(2)
                    continue

                print(f"[MUSIC] Guild found: {guild.name}")

                # -------------------------------------------------
                # Set state BEFORE playback
                # -------------------------------------------------
                player.current = track
                player.is_playing = True

                print(f"[MUSIC] Now playing: {track.title}")
                print("[MUSIC] Calling voice_bridge.play()")

                # -------------------------------------------------
                # Play through Lavalink
                # -------------------------------------------------
                played = await voice_bridge.play(
                    guild,
                    track
                )

                print(f"[MUSIC] play() returned: {played}")

                if not played:
                    player.current = None
                    player.is_playing = False

                    await asyncio.sleep(2)
                    continue

                # -------------------------------------------------
                # Wait for Lavalink playback to finish
                # -------------------------------------------------
                vc = guild.voice_client

                if vc:

                    print("[MUSIC] Waiting for track completion")

                    while vc.playing or vc.paused:
                        await asyncio.sleep(1)

                print("[MUSIC] Track finished")

                # -------------------------------------------------
                # Clear current track
                # -------------------------------------------------
                player.current = None
                player.is_playing = False

        except asyncio.CancelledError:
            pass

        except Exception as e:
            print(
                f"[MusicController] Error in guild "
                f"{guild_id}: {e}"
            )

        finally:
            self.running[guild_id] = False

    # =====================================================
    # UTILITIES
    # =====================================================

    def is_running(self, guild_id: int) -> bool:
        return self.running.get(guild_id, False)

    async def restart(self, guild_id: int):
        self.stop_loop(guild_id)

        await asyncio.sleep(1)

        await self.start_loop(guild_id)


music_controller = MusicController()