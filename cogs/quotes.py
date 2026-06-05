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


class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.initialized = False

    # =====================================================
    # INIT DB
    # =====================================================
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

    # =====================================================
    # SHARED HELPERS
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
    # PREFIX COMMANDS
    # =====================================================
    @commands.command(name="addquote")
    async def addquote_prefix(self, ctx, category: str, *, content: str):
        if not ctx.guild:
            return await ctx.send("Guild only command.")

        try:
            await self.add_quote(ctx.guild.id, category, content, ctx.author.id)
            await ctx.send("✅ Quote added.")
        except Exception as e:
            print("[DB] INSERT FAILED:", e)
            await ctx.send("❌ Failed to add quote.")

    @commands.command(name="quote")
    async def quote_prefix(self, ctx, category: str):
        if not ctx.guild:
            return await ctx.send("Guild only command.")

        try:
            result = await self.get_quote(ctx.guild.id, category)

            if not result:
                return await ctx.send("No quotes found.")

            await ctx.send(f"💬 {result}")

        except Exception as e:
            print("[DB] FETCH FAILED:", e)
            await ctx.send("❌ Error fetching quote.")

    # =====================================================
    # SLASH GROUP
    # =====================================================
    quote_group = app_commands.Group(
        name="quote",
        description="Quote system"
    )

    @quote_group.command(name="add")
    async def quote_add(self, interaction: discord.Interaction, category: str, content: str):
        if interaction.guild is None:
            return await interaction.response.send_message("Guild only command.", ephemeral=True)

        try:
            await self.add_quote(
                interaction.guild.id,
                category,
                content,
                interaction.user.id
            )
            await interaction.response.send_message("✅ Quote added.", ephemeral=True)

        except Exception as e:
            print("[DB] INSERT FAILED:", e)
            await interaction.response.send_message("❌ Failed.", ephemeral=True)

    @quote_group.command(name="get")
    async def quote_get(self, interaction: discord.Interaction, category: str):
        if interaction.guild is None:
            return await interaction.response.send_message("Guild only command.", ephemeral=True)

        try:
            result = await self.get_quote(interaction.guild.id, category)

            if not result:
                return await interaction.response.send_message("No quotes found.", ephemeral=True)

            await interaction.response.send_message(f"💬 {result}")

        except Exception as e:
            print("[DB] FETCH FAILED:", e)
            await interaction.response.send_message("❌ Error.", ephemeral=True)


async def setup(bot: commands.Bot):
    cog = Quotes(bot)
    await bot.add_cog(cog)

    # IMPORTANT: register slash group properly
    bot.tree.add_command(cog.quote_group)