import asyncio
import wavelink

from services.music.manager import music_manager
from services.music.player_message_manager import player_message_manager


class MusicEngine:

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks = {}
        self._idle_tasks = {}
        self._skip_guard = set()

    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        return player.guild.id

    # =====================================================
    def _lock(self, guild_id: int):
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    def _cancel_idle(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)
        if task:
            task.cancel()

    # =====================================================
    async def _notify_ui(self, player: wavelink.Player):
        try:
            guild = player.guild
            state = music_manager.get_player(guild.id)

            if not state.player_channel_id:
                return

            await player_message_manager.update(guild)

        except Exception as e:
            print(f"[UI ERROR] {e}")

    # =====================================================
    async def _play_next(self, player: wavelink.Player):

        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                state.current = None
                await self._notify_ui(player)
                return

            self._cancel_idle(guild_id)

            state.current = track

            try:
                playable = getattr(track, "playable", None)

                if not playable:
                    results = await wavelink.Playable.search(
                        track.uri or track.title
                    )
                    playable = results[0] if results else None

                if not playable:
                    return await self._play_next(player)

                await player.play(playable)

                await self._notify_ui(player)

            except Exception as e:
                print(f"[PLAY ERROR] {e}")
                state.current = None
                await self._play_next(player)

    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        state = music_manager.get_player(self._guild_id(player))
        state.queue.add(track)
        self._cancel_idle(self._guild_id(player))

    async def start(self, player: wavelink.Player):
        state = music_manager.get_player(self._guild_id(player))
        if not state.current:
            await self._play_next(player)

    async def skip(self, player: wavelink.Player):
        try:
            await player.stop()
        except:
            pass
        await self._play_next(player)

    async def stop(self, player: wavelink.Player):
        state = music_manager.get_player(self._guild_id(player))
        state.queue.clear()
        state.current = None

        try:
            await player.stop()
        except:
            pass

        await self._notify_ui(player)


engine = MusicEngine()