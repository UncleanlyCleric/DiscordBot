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
            # =====================================================
            # 1. Resolve playable safely (NO duplicate search spam)
            # =====================================================
            playable = getattr(track, "playable", None)

            if not playable:
                results = await wavelink.Playable.search(
                    track.uri or track.title
                )

                if not results:
                    return

                # =================================================
                # 2. Handle Playlist vs Track correctly
                # =================================================
                if isinstance(results, wavelink.Playlist):
                    if not results.tracks:
                        return
                    playable = results.tracks[0]
                else:
                    playable = results[0]

            # =====================================================
            # 3. Volume (safe optional hook)
            # =====================================================
            try:
                volume = getattr(self, "get_volume", lambda _: 100)(guild_id)
                await player.set_volume(volume)
            except Exception:
                pass

            # =====================================================
            # 4. PLAY (Wavelink 4 correct entry point)
            # =====================================================
            await player.play(playable)

        except Exception as e:
            print(f"[ENGINE] play error: {e}")
            await self._play_next(player)