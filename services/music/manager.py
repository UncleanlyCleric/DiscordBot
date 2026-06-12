from dataclasses import dataclass, field
from typing import Any, Optional

from services.music.queue import MusicQueue


@dataclass
class MusicState:

    queue: MusicQueue = field(
        default_factory=MusicQueue
    )

    current: Any = None

    player_message_id: Optional[int] = None
    player_channel_id: Optional[int] = None

    current_started_at: Optional[float] = None
    current_duration: Optional[int] = None

    # =====================================================
    # PLAYBACK SETTINGS
    # =====================================================

    volume: int = 70

    loop_track: bool = False
    loop_queue: bool = False

    autoplay: bool = False
    dj_mode: bool = False

    # =====================================================
    # TRACK MEMORY
    # =====================================================

    last_track: Any = None

    history: list = field(
        default_factory=list
    )


class MusicManager:

    def __init__(self):

        self._states: dict[
            int,
            MusicState
        ] = {}

    def get_player(
        self,
        guild_id: int
    ) -> MusicState:

        if guild_id not in self._states:

            self._states[guild_id] = (
                MusicState()
            )

        return self._states[guild_id]

    def get_all(self):

        return self._states.values()

    # =====================================================
    # DJ MODE CHECK
    # =====================================================

    def is_dj(self, guild_id: int, member) -> bool:
        state = self.get_player(guild_id)

        # DJ mode OFF = everyone allowed
        if not state.dj_mode:
            return True

        # Admin override
        if member.guild_permissions.manage_guild:
            return True

        return False

    # =====================================================
    # TOGGLES
    # =====================================================

    def set_autoplay(self, guild_id: int, value: bool):
        self.get_player(guild_id).autoplay = value

    def set_dj_mode(self, guild_id: int, value: bool):
        self.get_player(guild_id).dj_mode = value

    # =====================================================
    # CORE PLAYBACK FLOW (ADD THESE HOOKS)
    # =====================================================

    async def on_track_end(self, guild_id: int):
        state = self.get_player(guild_id)

        # 1. LOOP TRACK
        if state.loop_track and state.current:
            await self.play(state.current, guild_id=guild_id)
            return

        # 2. NORMAL QUEUE CONTINUE
        if not state.queue.is_empty():
            await self.play_next(guild_id)
            return

        # 3. AUTOPLAY (ONLY WHEN QUEUE IS EMPTY)
        if state.autoplay and state.last_track:
            next_track = await self.fetch_autoplay(state.last_track)

            if next_track:
                state.queue.add(next_track)
                await self.play_next(guild_id)
                return

        # 4. NOTHING LEFT
        state.current = None

    async def play_next(self, guild_id: int):
        state = self.get_player(guild_id)

        if state.queue.is_empty():
            await self.on_track_end(guild_id)
            return

        next_track = state.queue.pop()

        state.last_track = state.current
        state.current = next_track

        await self.play(next_track, guild_id=guild_id)

    async def fetch_autoplay(self, last_track):
        """
        Simple autoplay fallback.
        Replace this later with Spotify/YouTube related logic.
        """
        return await self.search_track(last_track.title)

    # =====================================================
    # YOU MUST ALREADY HAVE THIS ELSEWHERE
    # (kept as placeholder to avoid function loss)
    # =====================================================

    async def play(self, track, guild_id: int):
        """
        Existing function assumed.
        Not modified.
        """
        state = self.get_player(guild_id)

        # IMPORTANT STATE UPDATE FOR AUTOPLAY
        state.last_track = state.current
        state.current = track

        # Your existing audio playback logic should already be here
        # DO NOT REMOVE OR REPLACE YOUR IMPLEMENTATION
        pass

    # =====================================================
    # REQUIRED EXTERNAL METHOD (ASSUMED EXISTS OR TO IMPLEMENT)
    # =====================================================

    async def search_track(self, query: str):
        """
        Placeholder for your existing search system.
        """
        raise NotImplementedError("Implement your search system here")


music_manager = MusicManager()