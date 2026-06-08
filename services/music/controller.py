import asyncio
from typing import Dict, Optional

import wavelink

from services.music.manager import music_manager


class MusicController:
    """
    SINGLE playback engine (ONLY ONE LOOP PER GUILD)
    """

    def __init__(self):
        self.running: Dict[int, bool] = {}
        self._tasks: Dict[int, asyncio.Task] = {}

    # =====================================================
    # START LOOP
    # =====================================================
    async def start_loop(self, guild_id: int):
        if self.running.get(guild_id):
            return

        self.running[guild_id] = True

        if guild_id not in self._tasks:
            self._tasks[guild_id] = asyncio.create_task(
                self._run_loop(guild_id)
            )

    # =====================================================
    # STOP LOOP
    # =====================================================
    def stop_loop(self, guild_id: int):
        self.running[guild_id] = False

        task = self._tasks.get(guild_id)
        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    # =====================================================
    # MAIN ENGINE LOOP
    # =====================================================
    async def _run_loop(self, guild_id: int):
        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                # idle
                if not player.is_playing:
                    await asyncio.sleep(0.5)
                    continue

                # get next track
                track = player.queue.next()

                if not track:
                    await asyncio.sleep(1)
                    continue

                # mark current
                player.current = track

                print(f"[MUSIC] Now playing: {track.title}")

                # resolve guild
                guild = None
                for node in wavelink.Pool.nodes.values():
                    bot = getattr(node, "_client", None)
                    if bot:
                        guild = bot.get_guild(guild_id)
                    if guild:
                        break

                if not guild:
                    await asyncio.sleep(1)
                    continue

                vc: wavelink.Player = guild.voice_client

                if not vc:
                    await asyncio.sleep(1)
                    continue

                # IMPORTANT: single search point ONLY HERE
                results = await wavelink.Playable.search(track.uri)

                if not results:
                    print("[MUSIC] No results")
                    await asyncio.sleep(1)
                    continue

                playable = results[0]

                try:
                    await vc.play(playable)
                except Exception as e:
                    print(f"[MUSIC] play failed: {e}")
                    continue

                # wait until track ends
                while vc.playing or vc.paused:
                    await asyncio.sleep(1)

                player.current = None

        except asyncio.CancelledError:
            pass

        finally:
            self.running[guild_id] = False


music_controller = MusicController()