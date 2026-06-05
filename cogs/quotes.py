import discord
from discord.ext import commands
import random
from utils.db import add, fetch_random, init

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init()

    # ---------------- ADD QUOTE ----------------
    @commands.hybrid_command(name="quote_add")
    async def quote_add(self, ctx, category: str, *, content: str):
        await add(ctx.guild.id, category, content, str(ctx.author))
        await ctx.send(f"Saved to `{category}`")

    # ---------------- GET QUOTE ----------------
    @commands.hybrid_command(name="quote")
    async def quote(self, ctx, category: str):
        rows = await fetch_random(ctx.guild.id, category)

        if not rows:
            await ctx.send("No quotes found.")
            return

        await ctx.send(random.choice(rows)[0])

    # ---------------- PREFIX FALLBACK ----------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content.startswith("!"):
            return

        if message.content.startswith("!quote"):
            return

        parts = message.content[1:].split(" ", 1)
        cat = parts[0]

        if len(parts) > 1:
            await add(message.guild.id, cat, parts[1], str(message.author))
            await message.channel.send("Saved.")
        else:
            rows = await fetch_random(message.guild.id, cat)
            if rows:
                await message.channel.send(random.choice(rows)[0])


async def setup(bot):
    await bot.add_cog(Quotes(bot))