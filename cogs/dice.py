import discord
from discord import app_commands
from discord.ext import commands
import random
import re

class Dice(commands.Cog):
DICE_REGEX = re.compile(
r"(?P<count>\d{1,3})?d(?P<sides>\d{1,4})"
r"(?P<keep>(kh|kl)\d+)?"
r"(?P<adv>[ad])?"
r"(?P<modifier>[+-]\d+)?$",
re.IGNORECASE
)

```
MAX_DICE = 100
MAX_SIDES = 1000

def __init__(self, bot: commands.Bot):
    self.bot = bot

def roll_dice(self, count: int, sides: int):
    return [random.randint(1, sides) for _ in range(count)]

@app_commands.command(
    name="roll",
    description="Roll dice (d20, d20a, d20d, 4d6kh3, 2d20kh1+5)"
)
async def roll(
    self,
    interaction: discord.Interaction,
    expression: str = "d20"
):
    expression = expression.replace(" ", "").lower()

    match = self.DICE_REGEX.fullmatch(expression)

    if not match:
        return await interaction.response.send_message(
            "❌ Invalid dice expression.\n\n"
            "Examples:\n"
            "`d20`\n"
            "`d20+5`\n"
            "`d20a`\n"
            "`d20d`\n"
            "`4d6kh3`\n"
            "`2d20kh1+5`",
            ephemeral=True
        )

    count = int(match.group("count") or 1)
    sides = int(match.group("sides"))
    keep = match.group("keep")
    adv = match.group("adv")
    modifier = int(match.group("modifier") or 0)

    # Advantage / Disadvantage shorthand
    if adv == "a":
        count = 2
        keep = "kh1"

    elif adv == "d":
        count = 2
        keep = "kl1"

    # Validation
    if count < 1:
        return await interaction.response.send_message(
            "❌ Must roll at least one die.",
            ephemeral=True
        )

    if count > self.MAX_DICE:
        return await interaction.response.send_message(
            f"❌ Maximum dice is {self.MAX_DICE}.",
            ephemeral=True
        )

    if sides < 2:
        return await interaction.response.send_message(
            "❌ Dice must have at least 2 sides.",
            ephemeral=True
        )

    if sides > self.MAX_SIDES:
        return await interaction.response.send_message(
            f"❌ Maximum sides is {self.MAX_SIDES}.",
            ephemeral=True
        )

    rolls = self.roll_dice(count, sides)

    kept_rolls = rolls.copy()
    dropped_rolls = []
    keep_text = None

    if keep:
        mode = keep[:2]
        keep_count = int(keep[2:])

        if keep_count < 1 or keep_count > len(rolls):
            return await interaction.response.send_message(
                "❌ Invalid keep value.",
                ephemeral=True
            )

        sorted_rolls = sorted(rolls)

        if mode == "kh":
            kept_rolls = sorted_rolls[-keep_count:]
            dropped_rolls = sorted_rolls[:-keep_count]
            keep_text = f"Keep Highest {keep_count}"

        elif mode == "kl":
            kept_rolls = sorted_rolls[:keep_count]
            dropped_rolls = sorted_rolls[keep_count:]
            keep_text = f"Keep Lowest {keep_count}"

    subtotal = sum(kept_rolls)
    total = subtotal + modifier

    # Build calculation string
    calculation = " + ".join(str(r) for r in kept_rolls)

    if modifier > 0:
        calculation += f" + {modifier}"

    elif modifier < 0:
        calculation += f" - {abs(modifier)}"

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
        name="All Rolls",
        value=" ".join(f"🎲 {r}" for r in rolls),
        inline=False
    )

    if keep_text:
        embed.add_field(
            name=keep_text,
            value=", ".join(map(str, kept_rolls)),
            inline=False
        )

    if dropped_rolls:
        embed.add_field(
            name="Dropped",
            value=", ".join(map(str, dropped_rolls)),
            inline=False
        )

    embed.add_field(
        name="Calculation",
        value=f"`{calculation}`",
        inline=False
    )

    embed.add_field(
        name="Total",
        value=f"**{total}**",
        inline=False
    )

    # Critical detection
    crit_text = None

    if sides == 20 and len(kept_rolls) == 1:

        final_roll = kept_rolls[0]

        if final_roll == 20:
            crit_text = "🌟 **Critical Success!**"

        elif final_roll == 1:
            crit_text = "💀 **Critical Failure!**"

    if crit_text:
        embed.add_field(
            name="Result",
            value=crit_text,
            inline=False
        )

    if adv == "a":
        embed.set_footer(
            text="Advantage"
        )

    elif adv == "d":
        embed.set_footer(
            text="Disadvantage"
        )

    await interaction.response.send_message(
        embed=embed
    )
```

async def setup(bot: commands.Bot):
await bot.add_cog(Dice(bot))
