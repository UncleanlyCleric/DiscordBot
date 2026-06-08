import discord
from discord import app_commands
from discord.ext import commands

from core.cog_base import BaseCog
from services.dice.roller import dice_roller


class DiceCog(BaseCog):

    # -------------------------
    # SLASH: ROLL
    # -------------------------

    @app_commands.command(
        name="roll",
        description="Roll dice (e.g. 4d6kh3, 2d20+5, etc.)"
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        expression: str
    ):
        try:
            result = dice_roller.parse(expression)

        except ValueError:
            await self.send_error(
                interaction,
                "Invalid dice expression."
            )
            return

        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Expression",
            value=result.expression,
            inline=False
        )

        embed.add_field(
            name="Rolls",
            value=", ".join(map(str, result.rolls)),
            inline=False
        )

        if result.kept != result.rolls:
            embed.add_field(
                name="Kept",
                value=", ".join(map(str, result.kept)),
                inline=False
            )

        embed.add_field(
            name="Total",
            value=str(result.total),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # SLASH: ADVANTAGE
    # -------------------------

    @app_commands.command(
        name="advantage",
        description="Roll with advantage (2d20kh1)"
    )
    async def advantage(self, interaction: discord.Interaction):
        result = dice_roller.advantage()

        await interaction.response.send_message(
            f"🎲 Advantage: {result.rolls} → **{result.total}**"
        )

    # -------------------------
    # SLASH: DISADVANTAGE
    # -------------------------

    @app_commands.command(
        name="disadvantage",
        description="Roll with disadvantage (2d20kl1)"
    )
    async def disadvantage(self, interaction: discord.Interaction):
        result = dice_roller.disadvantage()

        await interaction.response.send_message(
            f"🎲 Disadvantage: {result.rolls} → **{result.total}**"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DiceCog(bot))