import discord
from discord.ext import commands
from discord import app_commands

from utils.db import add, fetch_random, search, delete, edit, init


class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._initialized = False

    # =====================================================
    # DB INIT
    # =====================================================
    @commands.Cog.listener()
    async def on_ready(self):
        if self._initialized:
            return
        self._initialized = True

        await init()

    # =====================================================
    # RAW MESSAGE ROUTER (CALLED FROM BOT)
    # =====================================================
    async def handle_raw_message(self, message: discord.Message):
        content = message.content.strip()

        # -------------------------
        # !add<category> text
        # -------------------------
        if content.startswith("!add"):
            try:
                raw = content[4:]
                category, text = raw.split(" ", 1)

                await add(
                    guild_id=message.guild.id,
                    category=category.lower(),
                    content=text,
                    author_id=str(message.author.id)
                )

                await message.channel.send("✅ Quote added.")
            except:
                await message.channel.send("Usage: `!add<category> <text>`")
            return

        # -------------------------
        # !<category>
        # -------------------------
        if content.startswith("!") and len(content) > 1:
            category = content[1:].strip().lower()

            if " " in category:
                return

            result = await fetch_random(message.guild.id, category)

            if result:
                await message.channel.send(f"💬 {result}")

    # =====================================================
    # PREFIX COMMANDS
    # =====================================================
    @commands.command(name="searchquote")
    async def searchquote(self, ctx, *, query: str):
        results = await search(ctx.guild.id, query)

        if not results:
            return await ctx.send("No matches.")

        msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])
        await ctx.send(msg)

    @commands.command(name="delquote")
    async def delquote(self, ctx, quote_id: int):
        ok = await delete(quote_id, ctx.guild.id)
        await ctx.send("🗑️ Deleted" if ok else "Not found")

    @commands.command(name="editquote")
    async def editquote(self, ctx, quote_id: int, *, text: str):
        ok = await edit(quote_id, ctx.guild.id, text)
        await ctx.send("✏️ Updated" if ok else "Not found")

    # =====================================================
    # SLASH COMMANDS
    # =====================================================
    quote = app_commands.Group(name="quote", description="Quote system")

    @quote.command(name="add")
    async def slash_add(self, interaction: discord.Interaction, category: str, content: str):
        await add(
            interaction.guild.id,
            category,
            content,
            str(interaction.user.id)
        )

        await interaction.response.send_message("✅ Added", ephemeral=True)

    @quote.command(name="get")
    async def slash_get(self, interaction: discord.Interaction, category: str):
        result = await fetch_random(interaction.guild.id, category)

        if not result:
            return await interaction.response.send_message("No quotes", ephemeral=True)

        await interaction.response.send_message(f"💬 {result}")

    @quote.command(name="search")
    async def slash_search(self, interaction: discord.Interaction, query: str):
        results = await search(interaction.guild.id, query)

        msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])

        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))
    bot.tree.add_command(Quotes.quote)