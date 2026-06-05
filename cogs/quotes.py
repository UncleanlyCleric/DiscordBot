import discord
from discord.ext import commands

from utils.db import (
    init,
    add,
    fetch_random,
    search,
    delete,
    edit
)

# =====================================================
# 🎯 QUOTES COG
# =====================================================
class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.initialized = False

    # -------------------------------------------------
    # INIT DB ON READY (SAFE GUARANTEE)
    # -------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        if self.initialized:
            return

        try:
            await init()
            self.initialized = True
            print("[QUOTES] DB initialized successfully")
        except Exception as e:
            print("[QUOTES] DB init failed:", e)

    # -------------------------------------------------
    # ADD QUOTE
    # -------------------------------------------------
    @commands.hybrid_command(name="addquote")
    async def addquote(self, ctx: commands.Context, category: str, *, content: str):

        try:
            await add(
                guild_id=ctx.guild.id,
                category=category,
                content=content,
                author_id=str(ctx.author.id)
            )

            print(f"[DB] INSERT OK guild={ctx.guild.id} category={category}")

            await ctx.send("✅ Quote added.")

        except Exception as e:
            print("[DB] INSERT FAILED:", e)
            await ctx.send("❌ Failed to add quote.")

    # -------------------------------------------------
    # RANDOM QUOTE
    # -------------------------------------------------
    @commands.hybrid_command(name="quote")
    async def quote(self, ctx: commands.Context, category: str):

        try:
            result = await fetch_random(ctx.guild.id, category)

            if not result:
                return await ctx.send("No quotes found.")

            await ctx.send(f"💬 {result}")

        except Exception as e:
            print("[DB] FETCH FAILED:", e)
            await ctx.send("❌ Error fetching quote.")

    # -------------------------------------------------
    # SEARCH QUOTES
    # -------------------------------------------------
    @commands.hybrid_command(name="searchquote")
    async def searchquote(self, ctx: commands.Context, *, query: str):

        try:
            results = await search(ctx.guild.id, query)

            if not results:
                return await ctx.send("No matches found.")

            msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])

            await ctx.send(msg)

        except Exception as e:
            print("[DB] SEARCH FAILED:", e)
            await ctx.send("❌ Search error.")

    # -------------------------------------------------
    # DELETE QUOTE
    # -------------------------------------------------
    @commands.hybrid_command(name="delquote")
    async def delquote(self, ctx: commands.Context, quote_id: int):

        try:
            ok = await delete(quote_id, ctx.guild.id)

            if ok:
                await ctx.send("🗑️ Deleted.")
            else:
                await ctx.send("Quote not found.")

        except Exception as e:
            print("[DB] DELETE FAILED:", e)
            await ctx.send("❌ Delete error.")

    # -------------------------------------------------
    # EDIT QUOTE
    # -------------------------------------------------
    @commands.hybrid_command(name="editquote")
    async def editquote(self, ctx: commands.Context, quote_id: int, *, new_content: str):

        try:
            ok = await edit(quote_id, ctx.guild.id, new_content)

            if ok:
                await ctx.send("✏️ Updated.")
            else:
                await ctx.send("Quote not found.")

        except Exception as e:
            print("[DB] EDIT FAILED:", e)
            await ctx.send("❌ Edit error.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))