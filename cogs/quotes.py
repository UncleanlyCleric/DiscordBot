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
# 🎯 QUOTES COG (DYNAMIC PREFIX ROUTER VERSION)
# =====================================================
class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # DB INIT (RUN ONCE)
    # =====================================================
    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self, "_initialized", False):
            return

        self._initialized = True

        try:
            await init()
            print("[QUOTES] DB initialized successfully")
        except Exception as e:
            print("[QUOTES] DB init failed:", e)

    # =====================================================
    # CORE DB HELPERS
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
    # 🚀 CUSTOM PREFIX ROUTER (!add<cat>, !<cat>)
    # =====================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.strip()

        # -------------------------------------------------
        # RESERVED COMMANDS 
        # -------------------------------------------------
        reserved = {
            "help",
            "ping",
            "stats",
            "quote",
            "addquote",
            "searchquote",
            "delquote",
            "editquote"
        }

        # =================================================
        # ➕ ADD QUOTE: !add<category> <text>
        # =================================================
        if content.startswith("!add"):
            try:
                after_prefix = content[4:]  # remove "!add"
                parts = after_prefix.split(" ", 1)

                if len(parts) < 2:
                    return await message.channel.send(
                        "Usage: `!add<category> <text>`"
                    )

                category = parts[0].strip().lower()
                text = parts[1].strip()

                if category in reserved:
                    return await message.channel.send(
                        "❌ That category is reserved."
                    )

                await self.add_quote(
                    message.guild.id,
                    category,
                    text,
                    message.author.id
                )

                await message.channel.send("✅ Quote added.")
                return

            except Exception as e:
                print("[DB] ADD FAILED:", e)
                await message.channel.send("❌ Failed to add quote.")
                return

        # =================================================
        # 💬 GET QUOTE: !<category>
        # =================================================
        if content.startswith("!"):
            try:
                category = content[1:].strip().lower()

                # ignore invalid usage like "! help"
                if not category or " " in category:
                    return

                if category in reserved:
                    return

                result = await self.get_quote(message.guild.id, category)

                if not result:
                    return await message.channel.send("No quotes found.")

                await message.channel.send(f"💬 {result}")

            except Exception as e:
                print("[DB] FETCH FAILED:", e)
                await message.channel.send("❌ Error fetching quote.")

    # =====================================================
    # 🔎 PREFIX COMMANDS (still supported)
    # =====================================================
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
    # 🌐 SLASH COMMAND GROUP (/quote)
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
# BOT SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))