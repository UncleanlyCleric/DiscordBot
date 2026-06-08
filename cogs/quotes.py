import discord
from discord import app_commands
from discord.ext import commands

from core.cog_base import BaseCog
from services.quotes.service import quote_service


class QuotesCog(BaseCog):
    """
    Quotes system:
    - slash commands (primary)
    - legacy ! commands (minimal support)
    - per-guild SQL storage
    """

    # -------------------------
    # SLASH: ADD QUOTE
    # -------------------------

    @app_commands.command(
        name="quote_add",
        description="Add a quote to a category."
    )
    @app_commands.describe(
        category="Quote category (e.g. movies, games, etc.)",
        text="The quote text"
    )
    async def quote_add(
        self,
        interaction: discord.Interaction,
        category: str,
        text: str
    ):
        await self.ensure_guild(interaction.guild_id)

        quote_id = await quote_service.add_quote(
            guild_id=interaction.guild_id,
            category=category,
            text=text,
            author_id=interaction.user.id
        )

        embed = discord.Embed(
            title="Quote Added",
            description=f"Saved to `{category}`",
            color=discord.Color.green()
        )
        embed.add_field(name="ID", value=str(quote_id), inline=True)
        embed.add_field(name="Text", value=text, inline=False)

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # SLASH: RANDOM QUOTE
    # -------------------------

    @app_commands.command(
        name="quote",
        description="Get a random quote (optionally by category)."
    )
    @app_commands.describe(
        category="Optional category filter"
    )
    async def quote(
        self,
        interaction: discord.Interaction,
        category: str | None = None
    ):
        await self.ensure_guild(interaction.guild_id)

        quote = await quote_service.get_random_quote(
            guild_id=interaction.guild_id,
            category=category
        )

        if not quote:
            await self.send_error(
                interaction,
                "No quotes found."
            )
            return

        embed = discord.Embed(
            title="💬 Quote",
            description=quote["quote_text"],
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="Category",
            value=quote["category"],
            inline=True
        )

        embed.add_field(
            name="ID",
            value=str(quote["id"]),
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # SLASH: CATEGORIES
    # -------------------------

    @app_commands.command(
        name="quote_categories",
        description="List all quote categories."
    )
    async def quote_categories(
        self,
        interaction: discord.Interaction
    ):
        await self.ensure_guild(interaction.guild_id)

        categories = await quote_service.get_categories(
            interaction.guild_id
        )

        if not categories:
            await self.send_error(
                interaction,
                "No categories found."
            )
            return

        embed = discord.Embed(
            title="Quote Categories",
            description="\n".join(f"• {c}" for c in categories),
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    # -------------------------
    # SLASH: DELETE QUOTE
    # -------------------------

    @app_commands.command(
        name="quote_delete",
        description="Delete a quote by ID."
    )
    @app_commands.describe(
        quote_id="The ID of the quote to delete"
    )
    async def quote_delete(
        self,
        interaction: discord.Interaction,
        quote_id: int
    ):
        await self.ensure_guild(interaction.guild_id)

        success = await quote_service.delete_quote(
            guild_id=interaction.guild_id,
            quote_id=quote_id
        )

        if not success:
            await self.send_error(
                interaction,
                "Quote not found."
            )
            return

        await self.send_success(
            interaction,
            f"Quote `{quote_id}` deleted."
        )

    # -------------------------
    # LEGACY COMMANDS (!)
    # -------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        content = message.content.strip()

        # -------------------------
        # !add <category> <text>
        # -------------------------

        if content.startswith("!add "):
            parts = content.split(" ", 2)

            if len(parts) < 3:
                return

            _, category, text = parts

            await self.ensure_guild(message.guild.id)

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

        # -------------------------
        # !<category>
        # -------------------------

        if content.startswith("!") and len(content) > 1:
            category = content[1:].split(" ")[0]

            await self.ensure_guild(message.guild.id)

            quote = await quote_service.get_random_quote(
                guild_id=message.guild.id,
                category=category
            )

            if quote:
                await message.channel.send(
                    f"💬 {quote['quote_text']}"
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(QuotesCog(bot))