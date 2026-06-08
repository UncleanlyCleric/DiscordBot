class MusicController:
    def __init__(self):
        self.running = {}
        self._tasks = {}

    # =====================================================
    # REQUIRED METHOD (YOU ARE MISSING THIS)
    # =====================================================
    async def start_loop(self, guild_id: int):
        if self.running.get(guild_id):
            return

        self.running[guild_id] = True

        if guild_id not in self._tasks:
            self._tasks[guild_id] = asyncio.create_task(
                self._run_loop(guild_id)
            )

    def stop_loop(self, guild_id: int):
        self.running[guild_id] = False

        task = self._tasks.get(guild_id)
        if task:
            task.cancel()
            self._tasks.pop(guild_id, None)

    async def _run_loop(self, guild_id: int):
        from services.music.manager import music_manager
        from services.music.lavalink.bridge import voice_bridge
        import wavelink
        import asyncio

        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                if not player.is_playing:
                    await asyncio.sleep(1)
                    continue

                track = player.current or player.queue.next()

                if not track:
                    await asyncio.sleep(2)
                    continue

                player.current = track
                player.is_playing = True

                print(f"[MUSIC] Now playing: {track.title}")

                # get guild
                guild = None
                for node in wavelink.Pool.nodes.values():
                    bot = getattr(node, "_client", None)
                    if bot:
                        guild = bot.get_guild(guild_id)
                    if guild:
                        break

                if not guild:
                    await asyncio.sleep(2)
                    continue

                await voice_bridge.play(guild, track)

                vc = guild.voice_client
                if vc:
                    while vc.playing or vc.paused:
                        await asyncio.sleep(1)

                player.current = None

        except asyncio.CancelledError:
            pass