import asyncio
import random
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 engine.

    - No voice disconnect logic here
    - Pure playback + queue logic
    - Safe concurrency handling
    """

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}

    # -------------------------------------------------
    # SAFE GUILD RESOLUTION
    # -------------------------------------------------
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        raise RuntimeError("Cannot resolve guild id")

    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # -------------------------------------------------
    # ENQUEUE (single entry point)
    # -------------------------------------------------
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        if not player.playing:
            await self._play_next(player)

    # -------------------------------------------------
    # PLAY NEXT
    # -------------------------------------------------
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                state.is_idle = True
                return

            state.current = track
            state.is_idle = False

            try:
                results = await wavelink.Playable.search(track.uri or track.title)

                if not results:
                    return

                await player.play(results[0])

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                await self._play_next(player)

    # -------------------------------------------------
    # SKIP
    # -------------------------------------------------
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

        await self._play_next(player)

    # -------------------------------------------------
    # STOP (NO DISCONNECT HERE)
    # -------------------------------------------------
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

    # -------------------------------------------------
    # SHUFFLE (NEW)
    # -------------------------------------------------
    async def shuffle(self, player: wavelink.Player):
        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        tracks = state.queue.all()
        random.shuffle(tracks)

        state.queue.clear()
        for t in tracks:
            state.queue.add(t)

    # -------------------------------------------------
    # VOLUME (NEW)
    # -------------------------------------------------
    async def set_volume(self, player: wavelink.Player, volume: int):
        volume = max(0, min(100, volume))

        try:
            await player.set_volume(volume)
        except Exception as e:
            print(f"[ENGINE] volume error: {e}")


engine = MusicEngine()