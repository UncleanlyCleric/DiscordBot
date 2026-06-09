import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:

    IDLE_TIMEOUT = 15

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}
        self._skip_guard: set[int] = set()

    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)
        if guild:
            return guild.id
        if hasattr(player, "_guild") and player._guild:
            return player._guild.id
        raise RuntimeError("Cannot resolve guild id")

    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # =====================================================
    def _cancel_idle(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    # =====================================================
    async def _idle_disconnect(self, player: wavelink.Player):
        await asyncio.sleep(self.IDLE_TIMEOUT)

        guild_id = self._guild_id(player)
        state = music_manager.get_player(guild_id)

        if state.current or state.queue.all():
            return

        try:
            await player.disconnect()
        except Exception:
            pass

    # =====================================================
    async def _notify_ui(self, player: wavelink.Player):
        try:
            from services.music.player_message_manager import player_message_manager
            guild = player.guild

            if not guild:
                print("[UI] notify skipped: no guild")
                return

            print("[UI] notify called")
            await player_message_manager.update(guild)

        except Exception as e:
            print(f"[UI] notify error: {e}")

    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)
        state.queue.add(track)

        print(f"[QUEUE] added track -> {getattr(track, 'title', 'unknown')}")

        self._cancel_idle(guild_id)

    # =====================================================
    async def _play_next(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        async with self._lock(guild_id):

            state = music_manager.get_player(guild_id)

            track = state.queue.next()

            if not track:
                print("[ENGINE] queue empty")

                state.current = None

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                await self._notify_ui(player)
                return

            print(f"[ENGINE] playing -> {getattr(track, 'title', 'unknown')}")

            state.current = track

            try:
                playable = getattr(track, "playable", None)

                if not playable:
                    results = await wavelink.Playable.search(
                        track.uri or track.title
                    )

                    if not results:
                        print("[ENGINE] no playable result")
                        return

                    playable = results[0]

                await player.play(playable)

                await self._notify_ui(player)

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                state.current = None
                await self._play_next(player)

    # =====================================================
    async def handle_track_end(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        if guild_id in self._skip_guard:
            print("[ENGINE] skip guard consumed")
            self._skip_guard.discard(guild_id)
            return

        print("[ENGINE] track ended -> advancing")
        await self._play_next(player)

    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        print("[ENGINE] skip triggered")

        self._skip_guard.add(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        self._skip_guard.discard(guild_id)

        await self._play_next(player)

    # =====================================================
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        print("[ENGINE] stop triggered")

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        self._cancel_idle(guild_id)

        try:
            await player.stop()
        except Exception:
            pass

        await self._notify_ui(player)


engine = MusicEngine()