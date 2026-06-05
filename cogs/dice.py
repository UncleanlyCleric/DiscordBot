import discord
from discord import app_commands
from discord.ext import commands
import random
import re


class Dice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # 🔥 THIS IS THE CRITICAL FIX
        bot.tree.add_command(self.roll)

    DICE_REGEX = re.compile(
        r"(?P<count>\d{1,3})?d(?P<sides>\d{1,4})"
        r"(?P<modifier>[+-]\d+)?"
    )

    MAX_DICE = 100
    MAX_SIDES = 1000

    def roll_once(self, count, sides):
        return [random.randint(1, sides) for _ in range(count)]

    @app_commands.command(name="roll", description="Roll dice")
    async def roll(self, interaction: discord.Interaction, expression: str = "d20"):

        match = self.DICE_REGEX.fullmatch(expression.replace(" ", ""))

        if not match:
            return await interaction.response.send_message(
                "Invalid format",
                ephemeral=True
            )

        count = int(match.group("count") or 1)
        sides = int(match.group("sides"))
        modifier = int(match.group("modifier") or 0)

        rolls = self.roll_once(count, sides)
        total = sum(rolls) + modifier

        embed = discord.Embed(title="🎲 Roll", color=discord.Color.blurple())
        embed.add_field(name="Rolls", value=str(rolls), inline=False)
        embed.add_field(name="Total", value=str(total), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dice(bot))