import re
import random
import discord
from discord import app_commands
from discord.ext import commands


# =====================================================
# 🎲 DICE PARSER
# =====================================================
DICE_REGEX = re.compile(
    r"(?P<count>\d{1,3})?d(?P<sides>\d{1,4})"
    r"(?P<modifier>[+-]\d+)?"
    r"(kh(?P<keep_high>\d+)|kl(?P<keep_low>\d+))?"
    r"(?:\s+(?P<mode>adv|dis))?"
)

MAX_DICE = 100
MAX_SIDES = 1000


# =====================================================
# 🎲 DICE COG
# =====================================================
class Dice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -----------------------------
    # CORE ROLL HELPERS
    # -----------------------------
    def roll_once(self, count: int, sides: int):
        return [random.randint(1, sides) for _ in range(count)]

    # =====================================================
    # /roll COMMAND (SLASH ONLY - FIXED)
    # =====================================================
    @app_commands.command(
        name="roll",
        description="Roll dice (d20, 2d6+3, 4d6kh3, adv/dis)"
    )
    @app_commands.describe(expression="Dice expression like 2d6+3, d20, 4d6kh3 adv")
    async def roll(self, interaction: discord.Interaction, expression: str = "d20"):

        expression = expression.replace(" ", "").lower()
        match = DICE_REGEX.fullmatch(expression)

        if not match:
            return await interaction.response.send_message(
                "❌ Invalid format.\nTry: `d20`, `2d6+3`, `4d6kh3 adv`, `d20 dis`",
                ephemeral=True
            )

        count = int(match.group("count") or 1)
        sides = int(match.group("sides"))
        modifier = int(match.group("modifier") or 0)

        keep_high = match.group("keep_high")
        keep_low = match.group("keep_low")

        keep_high = int(keep_high) if keep_high else None
        keep_low = int(keep_low) if keep_low else None

        mode = match.group("mode")

        if count > MAX_DICE or sides > MAX_SIDES:
            return await interaction.response.send_message(
                f"❌ Limit exceeded: max `{MAX_DICE}d{MAX_SIDES}`",
                ephemeral=True
            )

        # -------------------------
        # BASE ROLL
        # -------------------------
        rolls = self.roll_once(count, sides)
        original_rolls = rolls.copy()

        # -------------------------
        # KEEP LOGIC
        # -------------------------
        if keep_high is not None:
            rolls.sort(reverse=True)
            rolls = rolls[:keep_high]
        elif keep_low is not None:
            rolls.sort()
            rolls = rolls[:keep_low]

        base_total = sum(rolls) + modifier

        # -------------------------
        # ADV / DIS MODE
        # -------------------------
        adv_data = None

        if mode in ("adv", "dis"):
            roll_a = self.roll_once(count, sides)
            roll_b = self.roll_once(count, sides)

            total_a = sum(roll_a) + modifier
            total_b = sum(roll_b) + modifier

            if mode == "adv":
                final_total = max(total_a, total_b)
                label = "ADVANTAGE"
            else:
                final_total = min(total_a, total_b)
                label = "DISADVANTAGE"

            adv_data = (roll_a, total_a, roll_b, total_b, label)
        else:
            final_total = base_total

        # -------------------------
        # EMBED OUTPUT
        # -------------------------
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
                name="Kept Dice",
                value=str(rolls),
                inline=False
            )

        if adv_data:
            roll_a, total_a, roll_b, total_b, label = adv_data

            embed.add_field(
                name=f"{label} A",
                value=f"{roll_a} → **{total_a}**",
                inline=False
            )

            embed.add_field(
                name=f"{label} B",
                value=f"{roll_b} → **{total_b}**",
                inline=False
            )

        embed.add_field(
            name="Modifier",
            value=str(modifier),
            inline=True
        )

        embed.add_field(
            name="Total",
            value=f"**{final_total}**",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Dice(bot))