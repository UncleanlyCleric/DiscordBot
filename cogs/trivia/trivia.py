import discord
from discord import app_commands
from discord.ext import commands

from .lobby import TriviaLobby
from .game import TriviaEngine
from .db import TriviaDB
from . import questions


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = {}
        self.db = TriviaDB()
        self.engine = TriviaEngine(bot, self.db)

    @app_commands.command(name="trivia_start")
    async def start(self, interaction: discord.Interaction):
        cid = interaction.channel.id

        self.lobbies[cid] = TriviaLobby(cid, interaction.user.id)
        self.lobbies[cid].add_player(interaction.user.id)

        await interaction.response.send_message("Lobby created!")

    @app_commands.command(name="trivia_join")
    async def join(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)
        if not lobby:
            return await interaction.response.send_message("No lobby.", ephemeral=True)

        lobby.add_player(interaction.user.id)
        await interaction.response.send_message("Joined!", ephemeral=True)

    @app_commands.command(name="fib_submit")
    async def fib_submit(self, interaction: discord.Interaction, text: str):
        lobby = self.lobbies.get(interaction.channel.id)

        if not lobby or lobby.mode != "fibbage":
            return await interaction.response.send_message("Not fibbage.", ephemeral=True)

        lobby.submissions[interaction.user.id] = text
        await interaction.response.send_message("Submitted!", ephemeral=True)

    @app_commands.command(name="trivia_begin")
    async def begin(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)

        if interaction.user.id != lobby.host_id:
            return await interaction.response.send_message("Not host.", ephemeral=True)

        await interaction.response.send_message("Starting...")

        await self.engine.run(lobby, interaction.channel, questions.QUESTIONS)

        del self.lobbies[interaction.channel.id]


async def setup(bot):
    await bot.add_cog(Trivia(bot))