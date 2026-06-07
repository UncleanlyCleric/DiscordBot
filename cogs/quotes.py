import discord
from discord.ext import commands
from discord import app_commands

from utils.db import add, fetch_random, search, delete, edit


class Quotes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =====================================================
    # SAFE SEND
    # =====================================================
    async def safe_send(self, channel: discord.abc.Messageable, content: str):
        try:
            await channel.send(content)
        except discord.Forbidden:
            pass
        except Exception as e:
            self.bot.logger.error(f"SAFE_SEND ERROR: {e}")

    # =====================================================
    # RAW MESSAGE HANDLER
    # =====================================================
    async def handle_raw_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        content = message.content.strip()

        print(f"[QUOTES DEBUG] raw: {content}")

        # =================================================
        # IGNORE REAL COMMANDS (FIXED SAFETY FILTER)
        # =================================================
        if content.startswith("!"):
            cmd = content[1:].split(" ", 1)[0].lower()

            # Let real bot commands pass through normally
            if cmd in ["help", "play", "skip", "stop", "quote", "searchquote", "delquote", "editquote"]:
                return

            # =================================================
            # ➕ !add<category> <text>
            # =================================================
            if cmd.startswith("add"):
                try:
                    raw = content[4:].strip()

                    if not raw:
                        await self.safe_send(message.channel, "Usage: `!add<category> <text>`")
                        return

                    parts = raw.split(" ", 1)
                    if len(parts) != 2:
                        await self.safe_send(message.channel, "Usage: `!add<category> <text>`")
                        return

                    category, text = parts
                    category = category.lower().strip()

                    print(f"[QUOTES DEBUG] add -> category={category}, text={text}")

                    await add(
                        guild_id=message.guild.id,
                        category=category,
                        content=text,
                        author_id=str(message.author.id)
                    )

                    await self.safe_send(message.channel, f"✅ Added to `{category}`")

                except Exception as e:
                    self.bot.logger.error(f"ADD QUOTE ERROR: {e}")
                    await self.safe_send(message.channel, "❌ Failed to add quote.")

                return

            # =================================================
            # 💬 !<category> (QUOTE FETCH)
            # =================================================
            category = cmd.lower().strip()

            print(f"[QUOTES DEBUG] fetch category={category}")

            try:
                result = await fetch_random(message.guild.id, category)

                if result:
                    await self.safe_send(message.channel, f"💬 {result}")

            except Exception as e:
                self.bot.logger.error(f"DB FETCH ERROR: {e}")

            return

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
    # SLASH COMMAND GROUP
    # =====================================================
    quote = app_commands.Group(
        name="quote",
        description="Quote system"
    )

    @quote.command(name="add")
    async def slash_add(self, interaction: discord.Interaction, category: str, content: str):
        await add(
            interaction.guild.id,
            category.lower(),
            content,
            str(interaction.user.id)
        )

        await interaction.response.send_message("✅ Quote added.", ephemeral=True)

    @quote.command(name="get")
    async def slash_get(self, interaction: discord.Interaction, category: str):
        result = await fetch_random(interaction.guild.id, category.lower())

        if not result:
            return await interaction.response.send_message(
                "No quotes found.",
                ephemeral=True
            )

        await interaction.response.send_message(f"💬 {result}")

    @quote.command(name="search")
    async def slash_search(self, interaction: discord.Interaction, query: str):
        results = await search(interaction.guild.id, query)

        if not results:
            return await interaction.response.send_message(
                "No matches found.",
                ephemeral=True
            )

        msg = "\n".join([f"`{r[0]}` [{r[1]}] {r[2]}" for r in results[:10]])
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))