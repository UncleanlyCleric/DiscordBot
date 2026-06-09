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

    IDLE_TIMEOUT = 15

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
    # IDLE TIMER
    # =====================================================
    def _cancel_idle_timer(self, guild_id: int):
        task = self._idle_tasks.pop(guild_id, None)

        if task and not task.done():
            print(f"[ENGINE] Cancelling idle timer guild={guild_id}")
            task.cancel()

    async def _idle_disconnect(self, player: wavelink.Player):
        """
        Disconnect after inactivity.
        """

        guild_id = self._guild_id(player)

        print(f"[ENGINE] Idle timer started guild={guild_id}")

        await asyncio.sleep(self.IDLE_TIMEOUT)

        print(f"[ENGINE] Idle timer expired guild={guild_id}")

        try:
            guild_id = self._guild_id(player)

            state = music_manager.get_player(guild_id)

            # -------------------------------------------------
            # SAFETY CHECKS
            # -------------------------------------------------
            if state.current is not None:
                print(
                    f"[ENGINE] Idle abort: current track exists "
                    f"guild={guild_id}"
                )
                return

            try:
                if player.playing:
                    print(
                        f"[ENGINE] Idle abort: player.playing "
                        f"guild={guild_id}"
                    )
                    return
            except Exception:
                pass

            try:
                if player.paused:
                    print(
                        f"[ENGINE] Idle abort: player.paused "
                        f"guild={guild_id}"
                    )
                    return
            except Exception:
                pass

            if state.queue.all():
                print(
                    f"[ENGINE] Idle abort: queue not empty "
                    f"guild={guild_id}"
                )
                return

            await player.disconnect()

            print(
                f"[ENGINE] Idle disconnect "
                f"guild={guild_id}"
            )

        except Exception as e:
            print(f"[ENGINE] Idle disconnect error: {e}")

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

        # new music means we're not idle
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

            print(
                f"[ENGINE] Next track="
                f"{getattr(track, 'title', None)} "
                f"guild={guild_id}"
            )

            # -------------------------------------------------
            # QUEUE EMPTY
            # -------------------------------------------------
            if not track:
                state.current = None

                if guild_id not in self._idle_tasks:
                    print(
                        f"[ENGINE] Queue empty, starting idle timer "
                        f"guild={guild_id}"
                    )

                    self._idle_tasks[guild_id] = asyncio.create_task(
                        self._idle_disconnect(player)
                    )

                return

            # track found -> cancel idle timer immediately
            self._cancel_idle_timer(guild_id)

            state.current = track

            try:
                # -------------------------------------------------
                # SMART PLAYABLE HANDLING
                # -------------------------------------------------
                playable = getattr(track, "playable", None)

                if not playable:
                    results = await wavelink.Playable.search(
                        track.uri or track.title
                    )

                    if not results:
                        return

                    playable = results[0]

                # -------------------------------------------------
                # OPTIONAL VOLUME HOOK
                # -------------------------------------------------
                try:
                    vol = getattr(self, "get_volume", None)

                    if callable(vol):
                        await player.set_volume(
                            vol(guild_id)
                        )

                except Exception:
                    pass

                print(
                    f"[ENGINE] Starting playback: "
                    f"{getattr(track, 'title', 'Unknown')}"
                )

                await player.play(playable)

            except Exception as e:
                print(f"[ENGINE] play error: {e}")

                try:
                    state.current = None
                except Exception:
                    pass

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