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
        self._ready = False

    # ---------------- INIT ----------------
    @commands.Cog.listener()
    async def on_ready(self):
        if self._ready:
            return
        self._ready = True
        await init()

    # ---------------- ADD ----------------
    @commands.hybrid_command(
        name="quote_add",
        description="Add a quote to a category"
    )
    async def quote_add(self, ctx, category: str, *, content: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        await add(ctx.guild.id, category, content, str(ctx.author.id))
        await ctx.send(f"Saved to `{category}`")

    # ---------------- RANDOM QUOTE ----------------
    @commands.hybrid_command(
        name="quote",
        description="Get a random quote from a category"
    )
    async def quote(self, ctx, category: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        quote = await fetch_random(ctx.guild.id, category)

        if not quote:
            return await ctx.send(f"No quotes found in `{category}`.")

        embed = discord.Embed(
            title=f"Quote - {category}",
            description=quote,
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed)

    # ---------------- SEARCH ----------------
    @commands.hybrid_command(
        name="quote_search",
        description="Search quotes by keyword"
    )
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

        for qid, category, content in results[:25]:
            embed.add_field(
                name=f"[{qid}] {category}",
                value=content[:100],
                inline=False
            )

        await ctx.send(embed=embed)

    # ---------------- DELETE ----------------
    @commands.hybrid_command(
        name="quote_delete",
        description="Delete a quote by ID"
    )
    async def quote_delete(self, ctx, quote_id: int):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        result = await delete(quote_id, ctx.guild.id)

        if not result:
            return await ctx.send("Quote not found.")

        await ctx.send(f"Deleted quote `{quote_id}`")

    # ---------------- EDIT ----------------
    @commands.hybrid_command(
        name="quote_edit",
        description="Edit an existing quote"
    )
    async def quote_edit(self, ctx, quote_id: int, *, new_content: str):
        if not ctx.guild:
            return await ctx.send("Servers only.")

        result = await edit(quote_id, ctx.guild.id, new_content)

        if not result:
            return await ctx.send("Quote not found.")

        await ctx.send(f"Updated quote `{quote_id}`")


async def setup(bot):
    await bot.add_cog(Quotes(bot))