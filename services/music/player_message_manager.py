import logging

from services.music.manager import music_manager
from services.music.ui.music_player_view import MusicPlayerView
from services.music.now_playing import build_now_playing_embed


class PlayerMessageManager:

    def __init__(self):
        # guild_id -> discord.Message
        self._messages = {}

    # =====================================================
    async def update(self, guild):

        state = music_manager.get_player(guild.id)

        if not state.player_channel_id:
            logging.warning("[UI] ABORT no channel_id guild=%s", guild.id)
            return

        channel = guild.get_channel(state.player_channel_id)

        if not channel:
            logging.warning("[UI] ABORT no channel guild=%s", guild.id)
            return

        embed = build_now_playing_embed(guild)
        view = MusicPlayerView()

        message = self._messages.get(guild.id)

        try:
            # =====================================================
            # SINGLE MESSAGE STRATEGY (NO DUPLICATES)
            # =====================================================
            if message:
                await message.edit(embed=embed, view=view)
                logging.info("[UI] updated message=%s", message.id)

            else:
                message = await channel.send(embed=embed, view=view)
                self._messages[guild.id] = message
                logging.info("[UI] created message=%s", message.id)

        except Exception:
            logging.exception("[UI] update failed")


player_message_manager = PlayerMessageManager()