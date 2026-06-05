import discord
from discord.ext import commands

from utils.db import (
    add,
    fetch_random,
    init,
    search,
    delete,
    edit
)


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------- INIT ----------------
    @commands.Cog.listener()
    async def on_ready(self):
        await init()

    # ---------------- ADD ----------------
    @commands.hybrid_command(name="quote_add")
    async def quote_add(self, ctx, category: str, *, content: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        await add(ctx.guild.id, category, content, str(ctx.author))
        await ctx.send(f"Saved to `{category}`")

    # ---------------- RANDOM QUOTE ----------------
    @commands.hybrid_command(name="quote")
    async def quote(self, ctx, category: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        quote = await fetch_random(ctx.guild.id, category)

        if not quote:
            return await ctx.send("No quotes found.")

        embed = discord.Embed(
            title=f"Quote - {category}",
            description=quote,
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed)

    # ---------------- SEARCH ----------------
    @commands.hybrid_command(name="quote_search")
    async def quote_search(self, ctx, *, query: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        results = await search(ctx.guild.id, query)

        if not results:
            return await ctx.send("No matches found.")

        embed = discord.Embed(
            title=f"Search results for '{query}'",
            color=discord.Color.green()
        )

        for qid, category, content in results:
            embed.add_field(
                name=f"[{qid}] {category}",
                value=content[:100],
                inline=False
            )

        await ctx.send(embed=embed)

    # ---------------- DELETE ----------------
    @commands.hybrid_command(name="quote_delete")
    async def quote_delete(self, ctx, quote_id: int):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        await delete(quote_id, ctx.guild.id)
        await ctx.send(f"Deleted quote `{quote_id}`")

    # ---------------- EDIT ----------------
    @commands.hybrid_command(name="quote_edit")
    async def quote_edit(self, ctx, quote_id: int, *, new_content: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        await edit(quote_id, ctx.guild.id, new_content)
        await ctx.send(f"Updated quote `{quote_id}`")


async def setup(bot):
    await bot.add_cog(Quotes(bot))