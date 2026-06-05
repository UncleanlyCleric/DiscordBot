import discord
from discord.ext import commands
from discord import app_commands

from utils.db import (
    init,
    add,
    fetch_random,
    search,
    delete,
    edit
)


# =====================================================
# 🎯 QUOTES COG (STABLE + NO DUPLICATE REGISTRATION)
# =====================================================
class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # DB INIT (SAFE: ONLY ONCE PER PROCESS)
    # =====================================================
    @commands.Cog.listener()
    async def on_ready(self):
        # safe guard: prevents repeated init on reconnects
        if getattr(self, "_initialized", False):
            return

        self._initialized = True

        try:
            await init()
            print("[QUOTES] DB initialized successfully")
        except Exception as e:
            print("[QUOTES] DB init failed:", e)

    # =====================================================
    # CORE HELPERS
    # =====================================================
    async def add_quote(self, guild_id, category, content, author_id):
        return await add(
            guild_id=guild_id,
            category=category,
            content=content,
            author_id=str(author_id)
        )

    async def get_quote(self, guild_id, category):
        return await fetch_random(guild_id, category)

    # =====================================================
    # PREFIX COMMANDS (!quote etc)
    # =====================================================
    @commands.command(name="addquote")
    async def addquote_prefix(self, ctx: commands.Context, category: str, *, content: str):
        if not ctx.guild:
            return await ctx.send("Guild-only command.")

        try:
            await self.add_quote(ctx.guild.id, category, content, ctx.author.id)
            await ctx.send("✅ Quote added.")
        except Exception as e:
            print("[DB] INSERT FAILED:", e)
            await ctx.send("❌ Failed to add quote.")

    @commands.command(name="quote")
    async def quote_prefix(self, ctx: commands.Context, category: str):
        if not ctx.guild:
            return await ctx.send("Guild-only command.")

        try:
            result = await self.get_quote(ctx.guild.id, category)

            if not result:
                return await ctx.send("No quotes found.")

            await ctx.send(f"💬 {result}")

        except Exception as e:
            print("[DB] FETCH FAILED:", e)
            await ctx.send("❌ Error fetching quote.")

    @commands.command(name="searchquote")
    async def searchquote_prefix(self, ctx: commands.Context, *, query: str):
        if not ctx.guild:
            return await ctx.send("Guild-only command.")

        try:
            results = await search(ctx.guild.id, query)

            if not results:
                return await ctx.send("No matches found.")

            msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])
            await ctx.send(msg)

        except Exception as e:
            print("[DB] SEARCH FAILED:", e)
            await ctx.send("❌ Search error.")

    @commands.command(name="delquote")
    async def delquote_prefix(self, ctx: commands.Context, quote_id: int):
        if not ctx.guild:
            return await ctx.send("Guild-only command.")

        try:
            ok = await delete(quote_id, ctx.guild.id)
            await ctx.send("🗑️ Deleted." if ok else "Quote not found.")
        except Exception as e:
            print("[DB] DELETE FAILED:", e)
            await ctx.send("❌ Delete error.")

    @commands.command(name="editquote")
    async def editquote_prefix(self, ctx: commands.Context, quote_id: int, *, new_content: str):
        if not ctx.guild:
            return await ctx.send("Guild-only command.")

        try:
            ok = await edit(quote_id, ctx.guild.id, new_content)
            await ctx.send("✏️ Updated." if ok else "Quote not found.")
        except Exception as e:
            print("[DB] EDIT FAILED:", e)
            await ctx.send("❌ Edit error.")

    # =====================================================
    # SLASH COMMAND GROUP (/quote ...)
    # =====================================================
    quote_group = app_commands.Group(
        name="quote",
        description="Quote system"
    )

    @quote_group.command(name="add", description="Add a quote")
    async def quote_add(self, interaction: discord.Interaction, category: str, content: str):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Guild-only command.",
                ephemeral=True
            )

        try:
            await self.add_quote(
                interaction.guild.id,
                category,
                content,
                interaction.user.id
            )

            await interaction.response.send_message(
                "✅ Quote added.",
                ephemeral=True
            )

        except Exception as e:
            print("[DB] INSERT FAILED:", e)
            await interaction.response.send_message(
                "❌ Failed to add quote.",
                ephemeral=True
            )

    @quote_group.command(name="get", description="Get a random quote")
    async def quote_get(self, interaction: discord.Interaction, category: str):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Guild-only command.",
                ephemeral=True
            )

        try:
            result = await self.get_quote(interaction.guild.id, category)

            if not result:
                return await interaction.response.send_message(
                    "No quotes found.",
                    ephemeral=True
                )

            await interaction.response.send_message(f"💬 {result}")

        except Exception as e:
            print("[DB] FETCH FAILED:", e)
            await interaction.response.send_message(
                "❌ Error fetching quote.",
                ephemeral=True
            )

    @quote_group.command(name="search", description="Search quotes")
    async def quote_search(self, interaction: discord.Interaction, query: str):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "Guild-only command.",
                ephemeral=True
            )

        try:
            results = await search(interaction.guild.id, query)

            if not results:
                return await interaction.response.send_message(
                    "No matches found.",
                    ephemeral=True
                )

            msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])

            await interaction.response.send_message(msg)

        except Exception as e:
            print("[DB] SEARCH FAILED:", e)
            await interaction.response.send_message(
                "❌ Search error.",
                ephemeral=True
            )


# =====================================================
# IMPORTANT: NO TREE REGISTRATION HERE
# (prevents CommandAlreadyRegistered)
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))