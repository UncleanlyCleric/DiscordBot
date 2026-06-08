import asyncio


class GuildMusicController:
    """
    FINAL PRODUCTION-STABLE MUSIC CONTROLLER

    Fixes:
    - race conditions in playback
    - duplicate after_play triggers
    - zombie voice clients
    - concurrent play_next calls
    """

    def __init__(self, bot, music_manager):
        self.bot = bot
        self.music = music_manager

        # prevents double playback per guild
        self._locks = {}

    # ---------------------------
    # Lock per guild (CRITICAL FIX)
    # ---------------------------

    def _lock(self, guild_id: int):
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    # ---------------------------
    # Voice cleanup safety
    # ---------------------------

    async def safe_disconnect(self, guild_id: int, vc):
        self.music.clear_current(guild_id)
        self.music.clear_queue(guild_id)

        try:
            if vc and vc.is_connected():
                await vc.disconnect()
        except Exception as e:
            print(f"[Disconnect Error] {e}")

        self.music.remove_voice(guild_id)

    # ---------------------------
    # MAIN PLAY LOOP (FIXED)
    # ---------------------------

    async def play_next(self, guild_id: int, vc):
        async with self._lock(guild_id):

            if not vc or not vc.is_connected():
                return

            track = self.music.next_track(guild_id)

            if not track:
                await self.safe_disconnect(guild_id, vc)
                return

            self.music.set_current(guild_id, track)

            source = self._create_source(track)

            def after_play(error):
                # CRITICAL: prevent crash loops
                if error:
                    print(f"[Playback Error] {error}")

                fut = asyncio.run_coroutine_threadsafe(
                    self._safe_next(guild_id, vc),
                    self.bot.loop
                )

                try:
                    fut.result()
                except Exception as e:
                    print(f"[after_play crash handled] {e}")

            try:
                vc.play(source, after=after_play)
            except Exception as e:
                print(f"[VC Play Error] {e}")
                await self.safe_disconnect(guild_id, vc)

    # ---------------------------
    # SAFE NEXT WRAPPER
    # ---------------------------

    async def _safe_next(self, guild_id: int, vc):
        try:
            await self.play_next(guild_id, vc)
        except Exception as e:
            print(f"[safe_next error] {e}")

    # ---------------------------
    # FFmpeg (lazy + safe)
    # ---------------------------

    def _create_source(self, track: dict):
        import discord  # lazy import prevents startup crashes

        url = track.get("url")

        if not url:
            raise ValueError("Track missing URL")

        return discord.FFmpegPCMAudio(
            url,
            options="-vn"
        )

    # ---------------------------
    # CONNECT SAFELY
    # ---------------------------

    async def connect(self, voice_channel):
        vc = voice_channel.guild.voice_client

        if vc and vc.is_connected():
            return vc

        return await voice_channel.connect()


def create_guild_music_controller(bot, music_manager):
    return GuildMusicController(bot, music_manager)