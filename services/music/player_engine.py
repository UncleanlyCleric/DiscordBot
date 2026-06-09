import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    Production-safe Wavelink 4 engine.

    Rules:
    - ONLY accepts wavelink.Player
    - NO discord imports
    - NO guild-based API usage
    """

    def __init__(self):
        self._locks: dict[int, asyncio.Lock] = {}
        self._idle_tasks: dict[int, asyncio.Task] = {}

    # =====================================================
    # SAFE GUILD RESOLVE
    # =====================================================
    def _guild_id(self, player: wavelink.Player) -> int:
        guild = getattr(player, "guild", None)

        if guild:
            return guild.id

        if hasattr(player, "_guild") and player._guild:
            return player._guild.id

        raise RuntimeError("Cannot resolve guild id from player")

    # =====================================================
    # LOCK PER GUILD
    # =====================================================
    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()

        return self._locks[guild_id]

    # =====================================================
    # IDLE TIMER MANAGEMENT
    # =====================================================
    def _cancel_idle_timer(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)

        if task and not task.done():
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        """
        Disconnect after 2 minutes of inactivity.
        """

        await asyncio.sleep(15)

        try:
            guild_id = self._guild_id(player)

            state = music_manager.get_player(guild_id)

            if state.current:
                return

            if state.queue.all():
                return

            await player.disconnect()

            print(
                f"[ENGINE] Idle disconnect "
                f"guild={guild_id}"
            )

        except Exception:
            pass

        finally:
            try:
                guild_id = self._guild_id(player)
                self._idle_tasks.pop(guild_id, None)
            except Exception:
                pass

    # =====================================================
    # ENQUEUE
    # =====================================================
    async def enqueue(self, player: wavelink.Player, track):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.add(track)

        # user added music -> cancel idle disconnect
        self._cancel_idle_timer(guild_id)

        # safer than player.playing during transitions
        if not state.current:
            await self._play_next(player)

    # =====================================================
    # PUBLIC NEXT
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

            # =================================================
            # QUEUE EMPTY
            # =================================================
            if not track:
                state.current = None

                if guild_id not in self._idle_tasks:
                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

            state.current = track

            try:
                # -------------------------------------------------
                # SMART PLAYABLE HANDLING (NO DOUBLE SEARCH BUG)
                # -------------------------------------------------
                playable = getattr(track, "playable", None)

                if not playable:
                    results = await wavelink.Playable.search(
                        track.uri or track.title
                    )

                    if not results:
                        return

                    playable = results[0]

                # music resumed -> cancel idle timer
                self._cancel_idle_timer(guild_id)

                # -------------------------------------------------
                # OPTIONAL: volume hook (safe ignore if missing)
                # -------------------------------------------------
                try:
                    vol = getattr(self, "get_volume", None)

                    if callable(vol):
                        await player.set_volume(
                            vol(guild_id)
                        )

                except Exception:
                    pass

                await player.play(playable)

            except Exception as e:
                print(f"[ENGINE] play error: {e}")

                await self._play_next(player)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.current = None

        try:
            await player.stop()
        except Exception:
            pass

        await self._play_next(player)

    # =====================================================
    # STOP
    # =====================================================
    async def stop(self, player: wavelink.Player):
        guild_id = self._guild_id(player)

        state = music_manager.get_player(guild_id)

        state.queue.clear()
        state.current = None

        self._cancel_idle_timer(guild_id)

        try:
            await player.stop()
        except Exception:
            pass


engine = MusicEngine()