import discord

from services.music.manager import music_manager
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:
    """
    Single source of truth for now-playing UI.
    """

    async def update(self, guild: discord.Guild):
        print("[UI] update() CALLED")

        state = music_manager.get_player(guild.id)

        channel_id = state.player_channel_id
        message_id = state.player_message_id

        print(f"[UI] state channel_id={channel_id} message_id={message_id}")

        if not channel_id:
            print("[UI] ABORT: no channel_id set")
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            try:
                print("[UI] channel not cached, fetching...")
                channel = await guild.fetch_channel(channel_id)
            except Exception as e:
                print(f"[UI] FAILED to fetch channel: {e}")
                return

        embed = build_now_playing_embed(state)

        from services.music.ui.music_player_view import MusicPlayerView

        # =====================================================
        # FIRST MESSAGE
        # =====================================================
        if not message_id:
            try:
                print("[UI] sending new now-playing message...")

                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

                print(f"[UI] created message id={msg.id}")

            except Exception as e:
                print(f"[UI] FAILED to send message: {e}")

            return

        # =====================================================
        # UPDATE EXISTING MESSAGE
        # =====================================================
        try:
            print("[UI] fetching existing message...")

            msg = await channel.fetch_message(message_id)

            await msg.edit(
                embed=embed,
                view=MusicPlayerView()
            )

            print("[UI] message updated successfully")

        except Exception as e:
            print(f"[UI] UPDATE FAILED: {e}")

            try:
                print("[UI] fallback: sending new message...")

                msg = await channel.send(
                    embed=embed,
                    view=MusicPlayerView()
                )

                state.player_message_id = msg.id
                state.player_channel_id = channel.id

                print(f"[UI] fallback created message id={msg.id}")

            except Exception as e2:
                print(f"[UI] FALLBACK FAILED: {e2}")


player_message_manager = PlayerMessageManager()