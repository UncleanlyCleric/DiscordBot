import asyncio
import random
import wavelink

from services.music.manager import music_manager


class MusicEngine:

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._volume: dict[int, int] = {}

    # =====================================================
    # GUILD ID
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id")

    # =====================================================
    # LOCK
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    # VOLUME
    # =====================================================
    def get_volume(self, guild_id: int) -> int:
        return self._volume.get(guild_id, 100)

    def set_volume(self, guild_id: int, value: int):
        self._volume[guild_id] = max(0, min(100, value))

    # =====================================================
    # SHUFFLE
    # =====================================================
    async def shuffle(self, player: wavelink.Player):

        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        queue = state.queue._queue
        random.shuffle(queue)

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):

        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        state.queue.add(track)

        if not player.playing:
            await self._play_next(player)

    # =====================================================
    # NEXT
    # =====================================================
    async def play_next(self, player: wavelink.Player):
        await self._play_next(player)

    # =====================================================
    # CORE ENGINE
    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                return

            state.current = track

            try:
                results = await wavelink.Playable.search(
                    track.uri or track.title
                )

                if not results:
                    return

                volume = self.get_volume(guild_id)

                try:
                    await player.set_volume(volume)
                except Exception:
                    pass

                await player.play(results[0])

            except Exception as e:
                print(f"[ENGINE] error: {e}")
                await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        state.current = None

        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()