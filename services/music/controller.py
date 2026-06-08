import asyncio
from typing import Dict

import wavelink

from services.music.manager import music_manager
from services.music.lavalink.bridge import voice_bridge


class MusicController:
    """
    Central playback orchestrator.

    Responsibilities:
    - consume guild queues
    - trigger Lavalink playback
    - prevent double loops
    - advance tracks safely
    """

    def __init__(self):
        self.running: Dict[int, bool] = {}
        self._tasks: Dict[int, asyncio.Task] = {}

    # =====================================================
    # LOOP CONTROL
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

    # =====================================================
    # MAIN LOOP
    # =====================================================

    async def _run_loop(self, guild_id: int):
        player = music_manager.get_player(guild_id)

        try:
            while self.running.get(guild_id):

                # -------------------------------------------------
                # IDLE WAIT (prevents CPU spin)
                # -------------------------------------------------
                if not player.is_playing:
                    await asyncio.sleep(1)
                    continue

                # -------------------------------------------------
                # GET NEXT TRACK
                # -------------------------------------------------
                track = player.current or player.queue.next()

                if not track:
                    await asyncio.sleep(2)
                    continue

                # Set state
                player.current = track
                player.is_playing = True

                print(f"[MUSIC] Now playing: {track.title}")

                # -------------------------------------------------
                # RESOLVE GUILD FROM WAVELINK NODE
                # -------------------------------------------------
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

                # -------------------------------------------------
                # PLAY VIA LAVALINK
                # -------------------------------------------------
                try:
                    await voice_bridge.play(guild, track)
                except Exception as e:
                    print(f"[MusicController] Playback error: {e}")
                    player.current = None
                    await asyncio.sleep(2)
                    continue

                # -------------------------------------------------
                # WAIT UNTIL TRACK FINISHES
                # -------------------------------------------------
                vc = guild.voice_client

                if vc:
                    try:
                        while vc and (vc.playing or vc.paused):
                            await asyncio.sleep(1)
                    except Exception:
                        pass

                # -------------------------------------------------
                # ADVANCE QUEUE
                # -------------------------------------------------
                player.current = None

        except asyncio.CancelledError:
            pass

        except Exception as e:
            print(f"[MusicController] Fatal error in guild {guild_id}: {e}")

        finally:
            self.running[guild_id] = False


# =====================================================
# SINGLETON EXPORT (CRITICAL FIX)
# =====================================================

music_controller = MusicController()