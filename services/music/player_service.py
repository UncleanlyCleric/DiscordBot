import wavelink


class PlayerService:

    async def connect(self, guild, channel):
        player: wavelink.Player = guild.voice_client

        if player:
            if player.channel != channel:
                await player.move_to(channel)
            return player

        return await channel.connect(cls=wavelink.Player)

    async def play(self, guild, track):
        player: wavelink.Player = guild.voice_client

        if not player:
            return False

        await player.play(track.playable)
        return True


player_service = PlayerService()