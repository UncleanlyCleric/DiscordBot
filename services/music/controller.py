import asyncio
from typing import Dict

import wavelink

from services.music.manager import music_manager
from services.music.lavalink.bridge import voice_bridge
from services.music.autoplay import autoplay_engine


class MusicController:
    """
    Central playback orchestrator.
    """

    def __init__(self):
        self.running: Dict[int, bool] = {}
        self._tasks: Dict[int, asyncio.Task] = {}

    async def start_loop(self, guild_id: int):
        if self.running.get(guild_id):
            return

        self.running[guild_id] = True
        self._tasks[guild_id] = asyncio.create_task(self._run_loop(guild_id))

    def stop_loop(self, guild_id: int):
        self.running[guild_id] = False

        task = self._tasks.get(guild_id)
        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    async def _run_loop(self, guild_id: int):
        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                guild = None
                for node in wavelink.Pool.nodes.values():
                    bot = getattr(node, "_client", None)
                    if bot:
                        guild = bot.get_guild(guild_id)
                        if guild:
                            break

                if not guild:
                    await asyncio.sleep(2)
                    continue

                vc = guild.voice_client

                # =================================================
                # PAUSE HANDLING (REAL STATE, NOT FAKE BOOL)
                # =================================================
                if vc and getattr(vc, "paused", False):
                    await asyncio.sleep(1)
                    continue

                track = player.current or player.queue.next()

                if not track:
                    track = autoplay_engine.generate(player.current)
                    if track:
                        player.queue.add(track)
                        track = player.queue.next()

                if not track:
                    await asyncio.sleep(2)
                    continue

                player.current = track

                print(f"[MUSIC] Now playing: {track.title}")

                await voice_bridge.play(guild, track)

                # Wait until track finishes
                vc = guild.voice_client
                if vc:
                    while vc.playing or vc.paused:
                        await asyncio.sleep(1)

                await player.skip()

        except asyncio.CancelledError:
            pass

        except Exception as e:
            print(f"[MusicController] Error in guild {guild_id}: {e}")

        finally:
            self.running[guild_id] = False

    def is_running(self, guild_id: int) -> bool:
        return self.running.get(guild_id, False)


music_controller = MusicController()