import discord
from discord.ext import commands
from typing import Optional

from core.database import db
from core.config import config


class BaseCog(commands.Cog):
    """
    Base class for all cogs.

    Provides:
    - shared database access
    - guild bootstrap helper
    - config access
    - logging helper pattern
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = db
        self.config = config

    # -------------------------
    # GUILD SAFETY LAYER
    # -------------------------

    async def ensure_guild(self, guild_id: Optional[int]):
        """
        Ensures guild exists in DB before any operation.
        Safe no-op for DM contexts.
        """
        if guild_id is None:
            return

        await self.db.ensure_guild(guild_id)

    # -------------------------
    # HELPERS
    # -------------------------

    def is_guild(self, interaction: discord.Interaction) -> bool:
        return interaction.guild is not None

    def get_guild_id(self, interaction: discord.Interaction) -> Optional[int]:
        if interaction.guild:
            return interaction.guild.id
        return None

    async def send_error(
        self,
        interaction: discord.Interaction,
        message: str
    ):
        """
        Unified error response format.
        """
        embed = discord.Embed(
            title="Error",
            description=message,
            color=discord.Color.red()
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def send_success(
        self,
        interaction: discord.Interaction,
        message: str
    ):
        """
        Unified success response format.
        """
        embed = discord.Embed(
            title="Success",
            description=message,
            color=discord.Color.green()
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)