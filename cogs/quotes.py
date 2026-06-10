import discord
from discord import app_commands
from discord.ext import commands

from core.cog_base import BaseCog
from services.quotes.service import quote_service


class QuotesCog(BaseCog):

    # -------------------------
    # ADD QUOTE
    # -------------------------

    @app_commands.command(name="quote_add", description="Add a quote.")
    async def quote_add(self, interaction: discord.Interaction, category: str, text: str):

        await self.ensure_guild(interaction.guild_id)

        quote_id = await quote_service.add_quote(
            guild_id=interaction.guild_id,
            category=category,
            text=text,
            author_id=interaction.user.id
        )

        embed = discord.Embed(
            title="Quote Added",
            description=f"Saved to `{category.strip().lower()}`",
            color=discord.Color.green()
        )
        embed.add_field(name="ID", value=str(quote_id))
        embed.add_field(name="Text", value=text, inline=False)

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # RANDOM QUOTE
    # -------------------------

    @app_commands.command(name="quote", description="Get a random quote.")
    async def quote(self, interaction: discord.Interaction, category: str | None = None):

        await self.ensure_guild(interaction.guild_id)

        quote = await quote_service.get_random_quote(
            guild_id=interaction.guild_id,
            category=category
        )

        if not quote:
            return await self.send_error(interaction, "No quotes found.")

        embed = discord.Embed(
            title="💬 Quote",
            description=quote["quote_text"],
            color=discord.Color.blurple()
        )
        embed.add_field(name="Category", value=quote["category"])
        embed.add_field(name="ID", value=str(quote["id"]))

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # CATEGORIES
    # -------------------------

    @app_commands.command(name="quote_categories", description="List categories.")
    async def quote_categories(self, interaction: discord.Interaction):

        await self.ensure_guild(interaction.guild_id)

        categories = await quote_service.get_categories(interaction.guild_id)

        if not categories:
            return await self.send_error(interaction, "No categories found.")

        embed = discord.Embed(
            title="Quote Categories",
            description="\n".join(f"• {c}" for c in categories),
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # DELETE
    # -------------------------

    @app_commands.command(name="quote_delete", description="Delete a quote.")
    async def quote_delete(self, interaction: discord.Interaction, quote_id: int):

        await self.ensure_guild(interaction.guild_id)

        success = await quote_service.delete_quote(
            guild_id=interaction.guild_id,
            quote_id=quote_id
        )

        if not success:
            return await self.send_error(interaction, "Quote not found.")

        await self.send_success(interaction, f"Quote `{quote_id}` deleted.")

    # -------------------------
    # LEGACY PREFIX COMMANDS
    # -------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.strip()

        # -------------------------
        # !add<category> <text>
        # -------------------------
        if content.startswith("!add"):
            await self.ensure_guild(message.guild.id)

            raw = content[4:].lstrip()  # remove "!add"

            if not raw:
                return

            split_index = raw.find(" ")

            if split_index == -1:
                await message.channel.send(
                    "❌ Usage: `!add<category> <text>` (example: `!addmovies hello world`)"
                )
                return

            category = raw[:split_index].strip().lower()
            text = raw[split_index + 1:].strip()

            if not text:
                await message.channel.send(
                    "❌ You need to provide quote text."
                )
                return

            quote_id = await quote_service.add_quote(
                guild_id=message.guild.id,
                category=category,
                text=text,
                author_id=message.author.id
            )

            await message.channel.send(
                f"✅ Quote saved under `{category}` (ID: {quote_id})"
            )
            return