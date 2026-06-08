from typing import Dict, Optional

from services.music.guild_player import GuildPlayer


class MusicManager:
    """
    Global registry for all guild players.
    """

    def __init__(self):
        self.players: Dict[int, GuildPlayer] = {}

    def get_player(self, guild_id: int) -> GuildPlayer:
        if guild_id not in self.players:
            self.players[guild_id] = GuildPlayer(guild_id)

        return self.players[guild_id]

    def remove_player(self, guild_id: int):
        if guild_id in self.players:
            del self.players[guild_id]

    def get_all(self):
        return self.players.values()


music_manager = MusicManager()