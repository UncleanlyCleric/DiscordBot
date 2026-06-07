import discord
from discord.ext import commands


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

```
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
},

"playlist": {
    "title": "📃 /playlist",
    "description": "Load a playlist into the queue.",
    "usage": [
        "/playlist <url>",
        "/playlist <url> true"
    ],
    "examples": [
        "Load playlist normally",
        "Load playlist shuffled"
    ]
},

"queue": {
    "title": "📜 /queue",
    "description": "View the current music queue.",
    "usage": [
        "/queue"
    ],
    "examples": [
        "Displays queued tracks"
    ]
},

"skip": {
    "title": "⏭ /skip",
    "description": "Skip the currently playing track.",
    "usage": [
        "/skip"
    ],
    "examples": [
        "Move to the next song"
    ]
},

"pause": {
    "title": "⏸ /pause",
    "description": "Pause playback.",
    "usage": [
        "/pause"
    ],
    "examples": [
        "Pause current track"
    ]
},

"resume": {
    "title": "▶️ /resume",
    "description": "Resume playback.",
    "usage": [
        "/resume"
    ],
    "examples": [
        "Continue current track"
    ]
},

"stop": {
    "title": "⏹ /stop",
    "description": "Stop playback and clear the queue.",
    "usage": [
        "/stop"
    ],
    "examples": [
        "Disconnect and clear music"
    ]
},

"shuffle": {
    "title": "🔀 /shuffle",
    "description": "Shuffle the current queue.",
    "usage": [
        "/shuffle"
    ],
    "examples": [
        "Randomize queued tracks"
    ]
},

"quote": {
    "title": "💬 Quotes",
    "description": "Store and retrieve quotes.",
    "usage": [
        "/quote add <category> <text>",
        "/quote get <category>",
        "/quote search <text>"
    ],
    "examples": [
        "/quote add movie May the Force be with you",
        "/quote get movie",
        "/quote search force"
    ]
},

"yes": {
    "title": "👍 Quote Trigger",
    "description": "Retrieve a random quote from the 'yes' category.",
    "usage": [
        "!yes"
    ],
    "examples": [
        "!yes"
    ]
},

"no": {
    "title": "👎 Quote Trigger",
    "description": "Retrieve a random quote from the 'no' category.",
    "usage": [
        "!no"
    ],
    "examples": [
        "!no"
    ]
},

"config": {
    "title": "⚙️ /config",
    "description": "View current server configuration.",
    "usage": [
        "/config"
    ],
    "examples": [
        "Displays configured settings"
    ]
},

"set_dj_role": {
    "title": "🎧 /set_dj_role",
    "description": "Set the DJ role used for music permissions.",
    "usage": [
        "/set_dj_role @Role"
    ],
    "examples": [
        "/set_dj_role DJ"
    ]
},

"set_markov_channel": {
    "title": "🧠 /set_markov_channel",
    "description": "Restrict Markov learning to one channel.",
    "usage": [
        "/set_markov_channel #channel"
    ],
    "examples": [
        "/set_markov_channel #just-some-bullshit"
    ]
},

"toggle_markov_training": {
    "title": "🧠 /toggle_markov_training",
    "description": "Enable or disable Markov learning.",
    "usage": [
        "/toggle_markov_training"
    ],
    "examples": [
        "Turns Markov training on or off"
    ]
},

"markov": {
    "title": "🧠 !markov",
    "description": "Generate text from the Markov brain.",
    "usage": [
        "!markov"
    ],
    "examples": [
        "Generate a random Markov sentence"
    ]
},

"brain": {
    "title": "🧠 !brain",
    "description": "View Markov personality traits.",
    "usage": [
        "!brain"
    ],
    "examples": [
        "Display chaos/coherence/talkativeness"
    ]
}





# =====================================================
# HELP DATA BUILDER
# =====================================================
def build_help_data(bot: commands.Bot):
    data = {}

    # -----------------------------------------
    # Hybrid / Prefix Commands
    # -----------------------------------------
    for cmd in bot.commands:

        if cmd.hidden:
            continue

        category = cmd.cog_name or "General"

        data.setdefault(category, [])

        data[category].append({
            "name": cmd.name,
            "description": cmd.description or "No description"
        })

    # -----------------------------------------
    # Slash Commands
    # -----------------------------------------
    for cmd in bot.tree.get_commands():

        # Group commands (/quote add)
        if isinstance(cmd, discord.app_commands.Group):

            category = cmd.name.title()

            data.setdefault(category, [])

            for sub in cmd.commands:
                data[category].append({
                    "name": f"{cmd.name} {sub.name}",
                    "description": sub.description or "No description"
                })

        else:
            category = "Slash Commands"

            data.setdefault(category, [])

            data[category].append({
                "name": cmd.name,
                "description": cmd.description or "No description"
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

    def current(self):
        return self.embeds[self.index]

    @discord.ui.button(
        label="⬅",
        style=discord.ButtonStyle.gray
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.index = max(0, self.index - 1)
        await self.update(interaction)

    @discord.ui.button(
        label="➡",
        style=discord.ButtonStyle.gray
    )
    async def next(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.index = min(
            len(self.embeds) - 1,
            self.index + 1
        )
        await self.update(interaction)

    async def update(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.edit_message(
            embed=self.current(),
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

    async def callback(
        self,
        interaction: discord.Interaction
    ):

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

            await interaction.response.edit_message(
                embed=embeds[0],
                view=view
            )

        else:

            await interaction.response.edit_message(
                embed=embeds[0],
                view=self.view
            )


# =====================================================
# MAIN VIEW
# =====================================================
class HelpView(discord.ui.View):
    def __init__(self, help_data):
        super().__init__(timeout=120)
        self.add_item(
            HelpSelect(help_data)
        )


# =====================================================
# HELP COG
# =====================================================
class Help(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="Show help information"
    )
    async def help(
        self,
        ctx: commands.Context,
        query: str = None
    ):

        help_data = build_help_data(self.bot)

        # =============================================
        # COMMAND HELP MODE
        # =============================================
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
                    value="\n".join(
                        f"`{line}`"
                        for line in data["usage"]
                    ),
                    inline=False
                )

                embed.add_field(
                    name="Examples",
                    value="\n".join(
                        data["examples"]
                    ),
                    inline=False
                )

                return await ctx.send(
                    embed=embed
                )

            return await ctx.send(
                embed=discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No help available for `{query}`",
                    color=discord.Color.red()
                )
            )

        # =============================================
        # MAIN HELP MENU
        # =============================================
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

        await ctx.send(
            embed=embed,
            view=view
        )


# =====================================================
# SETUP
# =====================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))