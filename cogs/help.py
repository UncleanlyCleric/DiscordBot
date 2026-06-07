import discord
from discord.ext import commands

# =====================================================
# HIDDEN / ADMIN FILTER
# =====================================================
HIDDEN_COMMANDS = {
    "admin",
    "set_admin",
    "ban",
    "kick",
    "reload",
}

# =====================================================
# COMMAND HELP DATA
# =====================================================
COMMAND_HELP = {
    "roll": {
        "title": "🎲 /roll",
        "description": "Roll dice using tabletop notation.",
        "usage": [
            "/roll d20",
            "/roll d20+5",
            "/roll d20a",
            "/roll d20d",
            "/roll 4d6kh3",
            "/roll 8d6kl4+2"
        ],
        "examples": [
            "d20 → Roll a d20",
            "d20+5 → Roll and add a modifier",
            "d20a → Advantage",
            "d20d → Disadvantage",
            "4d6kh3 → Keep highest 3",
            "4d6kl3 → Keep lowest 3"
        ]
    },

    "play": {
        "title": "🎵 /play",
        "description": "Search for and play music immediately.",
        "usage": [
            "/play song name",
            "/play artist - song",
            "/play youtube url",
            "/play spotify url"
        ],
        "examples": [
            "/play The Cure - Just Like Heaven",
            "/play https://youtube.com/...",
            "/play https://open.spotify.com/..."
        ]
    }
}

# =====================================================
# HELP DATA BUILDER
# =====================================================
def build_help_data(bot: commands.Bot):
    data = {}

    # -----------------------------------------
    # PREFIX / HYBRID COMMANDS
    # -----------------------------------------
    for cmd in bot.commands:

        if cmd.hidden or cmd.name in HIDDEN_COMMANDS:
            continue

        category = cmd.cog_name or "General"
        data.setdefault(category, [])

        help_entry = COMMAND_HELP.get(cmd.name)

        data[category].append({
            "name": cmd.name,
            "description": (
                help_entry["description"]
                if help_entry
                else (cmd.description or "No description")
            )
        })

    # -----------------------------------------
    # SLASH COMMANDS
    # -----------------------------------------
    for cmd in bot.tree.get_commands():

        if cmd.name in HIDDEN_COMMANDS:
            continue

        if isinstance(cmd, discord.app_commands.Group):

            category = cmd.name.title()
            data.setdefault(category, [])

            for sub in cmd.commands:

                if sub.name in HIDDEN_COMMANDS:
                    continue

                help_entry = COMMAND_HELP.get(sub.name)

                data[category].append({
                    "name": f"{cmd.name} {sub.name}",
                    "description": (
                        help_entry["description"]
                        if help_entry
                        else (sub.description or "No description")
                    )
                })

        else:

            category = "Slash Commands"
            data.setdefault(category, [])

            help_entry = COMMAND_HELP.get(cmd.name)

            data[category].append({
                "name": cmd.name,
                "description": (
                    help_entry["description"]
                    if help_entry
                    else (cmd.description or "No description")
                )
            })

    return data

# =====================================================
# PAGINATOR
# =====================================================
class HelpPager(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.index = 0

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
            embed=self.embeds[self.index],
            view=self
        )

# =====================================================
# CATEGORY SELECT MENU
# =====================================================
class HelpSelect(discord.ui.Select):
    def __init__(self, help_data):

        options = [
            discord.SelectOption(
                label=category,
                description=f"{len(commands)} commands"
            )
            for category, commands in help_data.items()
        ]

        super().__init__(
            placeholder="Select a category...",
            options=options
        )

        self.help_data = help_data

    async def callback(self, interaction: discord.Interaction):

        category = self.values[0]
        commands_list = self.help_data.get(category, [])

        embeds = []

        embed = discord.Embed(
            title=f"📚 {category}",
            color=discord.Color.blurple()
        )

        count = 0

        for cmd in commands_list:

            embed.add_field(
                name=f"/{cmd['name']}",
                value=cmd["description"],
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
# MAIN VIEW
# =====================================================
class HelpView(discord.ui.View):
    def __init__(self, help_data):
        super().__init__(timeout=120)
        self.add_item(HelpSelect(help_data))

# =====================================================
# HELP COG
# =====================================================
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show help information")
    async def help(self, ctx: commands.Context, query: str = None):

        help_data = build_help_data(self.bot)

        # -----------------------------------------
        # SPECIFIC COMMAND HELP
        # -----------------------------------------
        if query:

            query = query.lower()

            if query in COMMAND_HELP:

                data = COMMAND_HELP[query]

                embed = discord.Embed(
                    title=data["title"],
                    description=data["description"],
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="Usage",
                    value="\n".join(f"`{line}`" for line in data["usage"]),
                    inline=False
                )

                embed.add_field(
                    name="Examples",
                    value="\n".join(data["examples"]),
                    inline=False
                )

                try:
                    await ctx.author.send(embed=embed)

                    if ctx.interaction:
                        await ctx.send(
                            "📬 Check your DMs for help information.",
                            ephemeral=True
                        )
                    else:
                        await ctx.send("📬 Check your DMs for help information.")

                except discord.Forbidden:
                    await ctx.send(
                        "❌ I couldn't DM you. Enable DMs and try again."
                    )

                return

            await ctx.send(
                embed=discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No help available for `{query}`",
                    color=discord.Color.red()
                )
            )
            return

        # -----------------------------------------
        # MAIN HELP MENU
        # -----------------------------------------
        embed = discord.Embed(
            title="📖 Help Menu",
            description=(
                "Select a category below.\n\n"
                "**Popular Help Topics**\n"
                "`/help play`\n"
                "`/help playlist`\n"
                "`/help queue`\n"
                "`/help quote`\n"
                "`/help config`\n"
                "`/help roll`\n"
            ),
            color=discord.Color.blurple()
        )

        view = HelpView(help_data)

        try:
            await ctx.author.send(embed=embed, view=view)

            if ctx.interaction:
                await ctx.send(
                    "📬 Check your DMs for the help menu.",
                    ephemeral=True
                )
            else:
                await ctx.send("📬 Check your DMs for the help menu.")

        except discord.Forbidden:
            await ctx.send(
                "❌ I couldn't DM you. Enable DMs and try again."
            )

# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))