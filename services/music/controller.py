import asyncio
import wavelink

from services.music.manager import music_manager


class MusicController:

    def __init__(self):
        self.running = {}
        self._tasks = {}

    async def start_loop(self, guild_id: int):

        if self.running.get(guild_id):
            return

        self.running[guild_id] = True

        if guild_id not in self._tasks:
            self._tasks[guild_id] = asyncio.create_task(
                self._run(guild_id)
            )

    def stop_loop(self, guild_id: int):

        self.running[guild_id] = False

        task = self._tasks.get(guild_id)
        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    async def _run(self, guild_id: int):

        player_state = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                vc = player_state.guild.voice_client if player_state.guild else None

                if not vc or not isinstance(vc, wavelink.Player):
                    await asyncio.sleep(1)
                    continue

                track = player_state.queue.next()

                if not track:
                    await asyncio.sleep(1)
                    continue

                player_state.current = track

                print(f"[MUSIC] Now playing: {track.title}")

                playable = getattr(track, "_wavelink_track", None)

                if playable is None:
                    results = await wavelink.Playable.search(track.uri)
                    if not results:
                        continue
                    playable = results[0]

                await vc.play(playable)

                while vc.playing or vc.paused:
                    await asyncio.sleep(1)

                player_state.current = None

        except asyncio.CancelledError:
            pass


# =========================================================
# 🔥 THIS LINE IS REQUIRED OR IMPORT WILL FAIL
# =========================================================
music_controller = MusicController()