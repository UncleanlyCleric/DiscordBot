import re
import random
import discord
from discord.ext import commands


DICE_REGEX = re.compile(
    r"(?P<count>\d{1,3})?d(?P<sides>\d{1,4})"
    r"(?P<modifier>[+-]\d+)?"
    r"(kh(?P<keep_high>\d+)|kl(?P<keep_low>\d+))?"
)

MAX_DICE = 100
MAX_SIDES = 1000


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx, *, expression: str = "d20"):
        """
        Roll dice using notation like:
        d20, 2d6+3, 4d6kh3, 1d20-1
        """

        match = DICE_REGEX.fullmatch(expression.replace(" ", "").lower())
        if not match:
            return await ctx.send("Invalid format. Try `d20`, `2d6+3`, or `4d6kh3`.")

        count = int(match.group("count") or 1)
        sides = int(match.group("sides"))
        modifier = int(match.group("modifier") or 0)

        keep_high = match.group("keep_high")
        keep_low = match.group("keep_low")

        keep_high = int(keep_high) if keep_high else None
        keep_low = int(keep_low) if keep_low else None

        # Safety limits
        if count > MAX_DICE or sides > MAX_SIDES:
            return await ctx.send(
                f"Too many dice or sides. Max: {MAX_DICE}d{MAX_SIDES}"
            )

        # Roll dice
        rolls = [random.randint(1, sides) for _ in range(count)]

        original_rolls = rolls.copy()

        # Handle keep highest / lowest
        if keep_high is not None:
            rolls.sort(reverse=True)
            rolls = rolls[:keep_high]
        elif keep_low is not None:
            rolls.sort()
            rolls = rolls[:keep_low]

        total = sum(rolls) + modifier

        # Build response
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Expression",
            value=f"`{expression}`",
            inline=False
        )

        embed.add_field(
            name="Rolls",
            value=str(original_rolls),
            inline=False
        )

        if rolls != original_rolls:
            embed.add_field(
                name="Kept",
                value=str(rolls),
                inline=False
            )

        embed.add_field(
            name="Modifier",
            value=str(modifier),
            inline=True
        )

        embed.add_field(
            name="Total",
            value=f"**{total}**",
            inline=True
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Dice(bot))