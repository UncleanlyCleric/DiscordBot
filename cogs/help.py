import discord
from discord.ext import commands


# =====================================================
# 📦 HELP DATA BUILDER
# =====================================================
def build_help_data(bot: commands.Bot):
    data = {}

    for cmd in bot.commands:
        if cmd.hidden:
            continue

        category = cmd.cog_name or "Uncategorized"

        if category not in data:
            data[category] = []

        data[category].append(cmd)

    return data


# =====================================================
# 📄 PAGINATOR
# =====================================================
class HelpPager(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.index = 0

    def current(self):
        return self.embeds[self.index]

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.gray)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(0, self.index - 1)
        await self.update(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = min(len(self.embeds) - 1, self.index + 1)
        await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.current(),
            view=self
        )


# =====================================================
# 📚 CATEGORY SELECT MENU
# =====================================================
class HelpSelect(discord.ui.Select):
    def __init__(self, help_data):

        options = [
            discord.SelectOption(
                label=cat,
                description=f"{len(cmds)} commands"
            )
            for cat, cmds in help_data.items()
        ]

        super().__init__(
            placeholder="Select a category...",
            options=options
        )

        self.help_data = help_data

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]
        commands = self.help_data.get(category, [])

        embeds = []
        embed = discord.Embed(
            title=f"📚 {category}",
            color=discord.Color.blurple()
        )

        count = 0

        for cmd in commands:
            desc = cmd.description or "No description"

            embed.add_field(
                name=f"/{cmd.name}",
                value=desc,
                inline=False
            )

            count += 1

            if count == 25:
                embeds.append(embed)
                embed = discord.Embed(
                    title=f"📚 {category} (cont.)",
                    color=discord.Color.blurple()
                )
                count = 0

        embeds.append(embed)

        if len(embeds) > 1:
            view = HelpPager(embeds)
            await interaction.response.edit_message(embed=embeds[0], view=view)
        else:
            await interaction.response.edit_message(embed=embeds[0], view=self.view)


# =====================================================
# 🎛 MAIN VIEW
# =====================================================
class HelpView(discord.ui.View):
    def __init__(self, help_data):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(help_data))


# =====================================================
# 📖 HELP COG
# =====================================================
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="Show all bot commands"
    )
    async def help(self, ctx: commands.Context, query: str = None):

        help_data = build_help_data(self.bot)

        # =================================================
        # 🔍 SEARCH MODE (NOW INCLUDES ALIASES)
        # =================================================
        if query:
            query = query.lower()

            matches = []

            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue

                aliases = getattr(cmd, "aliases", [])

                if (
                    query in cmd.name.lower()
                    or any(query in a.lower() for a in aliases)
                ):
                    matches.append(cmd)

            if not matches:
                return await ctx.send(
                    embed=discord.Embed(
                        title="No results found",
                        description=f"No commands matching `{query}`",
                        color=discord.Color.red()
                    )
                )

            embed = discord.Embed(
                title=f"🔍 Results for '{query}'",
                color=discord.Color.green()
            )

            for cmd in matches[:25]:
                desc = cmd.description or "No description"

                embed.add_field(
                    name=f"/{cmd.name}",
                    value=desc,
                    inline=False
                )

            return await ctx.send(embed=embed)

        # =================================================
        # 📚 MAIN MENU
        # =================================================
        embed = discord.Embed(
            title="📖 Help Menu",
            description="Select a category or use `/help <command>`",
            color=discord.Color.blurple()
        )

        view = HelpView(help_data)
        await ctx.send(embed=embed, view=view)


# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))