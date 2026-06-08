import random
import discord
from discord.ext import commands

from utils.db import db


class QuotesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        db.connect()
        db.init_schema()

    @commands.command(name="addquote")
    async def add_quote(self, ctx, category: str, *, quote: str):
        category = category.lower()

        cur = db.cursor()

        cur.execute(
            """
            INSERT INTO quotes
            (guild_id, category, quote, author, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(ctx.guild.id),
                category,
                quote,
                str(ctx.author),
                str(ctx.author.id),
            ),
        )

        db.conn.commit()

        await ctx.send(f"Saved quote in **{category}**")

    @commands.command(name="quote")
    async def quote(self, ctx, category: str):
        category = category.lower()

        cur = db.cursor()

        cur.execute(
            """
            SELECT quote, author
            FROM quotes
            WHERE guild_id = ?
            AND category = ?
            """,
            (
                str(ctx.guild.id),
                category,
            ),
        )

        rows = cur.fetchall()

        if not rows:
            await ctx.send(f"No quotes found in **{category}**")
            return

        quote_text, author = random.choice(rows)

        embed = discord.Embed(
            title=f"{category.title()} Quote",
            description=quote_text,
            color=discord.Color.blurple(),
        )

        embed.set_footer(
            text=f"Added by {author or 'Unknown'}"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(QuotesCog(bot))