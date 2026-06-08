import asyncio
import wavelink

from services.music.manager import music_manager


class MusicEngine:
    """
    SINGLE SOURCE OF TRUTH FOR ALL PLAYBACK.
    """

    def __init__(self):
        self.locks = {}  # per-guild lock to prevent race conditions

    # =====================================================
    # INTERNAL LOCK
    # =====================================================
    def _lock(self, guild_id: int):
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()
        return self.locks[guild_id]

    # =====================================================
    # ENQUEUE + AUTO PLAY
    # =====================================================
    async def enqueue(self, guild: wavelink.Player, track):

        state = music_manager.get_player(guild.id)

        state.queue.add(track)

        if not guild.playing:
            await self.play_next(guild)

    # =====================================================
    # CORE PLAYBACK FUNCTION
    # =====================================================
    async def play_next(self, guild: wavelink.Player):

        async with self._lock(guild.id):

            state = music_manager.get_player(guild.id)

            # already playing
            if guild.playing:
                return

            track = state.queue.next()

            if not track:
                state.current = None
                return

            state.current = track

            try:
                playable = await wavelink.Playable.search(track.uri or track.title)

                if not playable:
                    return

                item = playable[0]

                await guild.play(item)

            except Exception as e:
                print(f"[ENGINE] play error: {e}")
                await self.play_next(guild)

    # =====================================================
    # SKIP
    # =====================================================
    async def skip(self, guild: wavelink.Player):
        try:
            await guild.stop()
        except Exception:
            pass

    # =====================================================
    # STOP (FULL RESET)
    # =====================================================
    async def stop(self, guild: wavelink.Player):

        state = music_manager.get_player(guild.id)

        state.queue.clear()
        state.current = None

        try:
            await guild.stop()
        except Exception:
            pass

    # =====================================================
    # TRACK END HANDLER
    # =====================================================
    async def on_track_end(self, guild: wavelink.Player):

        state = music_manager.get_player(guild.id)
        state.current = None

        await self.play_next(guild)


engine = MusicEngine()