import discord
from discord import app_commands
from discord.ext import commands

from utils.config import get, set_value


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------- CONFIG VIEW ----------------
    @app_commands.command(name="config")
    async def config(self, interaction: discord.Interaction):
        cfg = get(interaction.guild.id)

        embed = discord.Embed(title="Server Config", color=discord.Color.blurple())
        embed.add_field(name="DJ Role ID", value=str(cfg["dj_role_id"]))
        embed.add_field(name="Markov Channel", value=str(cfg["markov_channel_id"]))
        embed.add_field(name="Markov Training", value=str(cfg["markov_training"]))

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------- SET DJ ROLE ----------------
    @app_commands.command(name="set_dj_role")
    @app_commands.describe(role="DJ role to control music")
    async def set_dj_role(self, interaction: discord.Interaction, role: discord.Role):
        set_value(interaction.guild.id, "dj_role_id", role.id)
        await interaction.response.send_message(f"DJ role set to {role.name}", ephemeral=True)

    # ---------------- SET MARKOV CHANNEL ----------------
    @app_commands.command(name="set_markov_channel")
    async def set_markov_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        set_value(interaction.guild.id, "markov_channel_id", channel.id)
        await interaction.response.send_message(f"Markov locked to {channel.mention}", ephemeral=True)

    # ---------------- TOGGLE MARKOV TRAINING ----------------
    @app_commands.command(name="toggle_markov_training")
    async def toggle_markov_training(self, interaction: discord.Interaction):
        cfg = get(interaction.guild.id)

        new_state = not cfg["markov_training"]
        set_value(interaction.guild.id, "markov_training", new_state)

        await interaction.response.send_message(
            f"Markov training: **{new_state}**",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Config(bot))