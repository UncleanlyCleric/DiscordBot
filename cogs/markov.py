import os
import json
import gzip
import random
import asyncio
import discord
from discord.ext import commands

from markov_core import MarkovChain


# -----------------------------
# GUILD STATE
# -----------------------------

class GuildBrain:
    def __init__(self):
        self.model = MarkovChain()

        # evolving traits
        self.traits = {
            "chaos": 0.3,
            "coherence": 0.6,
            "talkativeness": 0.4
        }

        # feedback tracking window
        self.engagement = {
            "messages": 0,
            "replies": 0,
            "mentions": 0
        }

    def drift(self):
        """slow personality evolution"""
        for k in self.traits:
            self.traits[k] += random.uniform(-0.01, 0.01)
            self.traits[k] = max(0.0, min(1.0, self.traits[k]))


# -----------------------------
# MAIN COG
# -----------------------------

class MarkovCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds = {}

        os.makedirs("data", exist_ok=True)

        self.bot.loop.create_task(self.load_all())

        self.autosave_task = self.bot.loop.create_task(self.autosave_loop())
        self.chatter_task = self.bot.loop.create_task(self.random_chatter_loop())
        self.dream_task = self.bot.loop.create_task(self.dream_loop())

    # -------------------------
    # GUILD HELPERS
    # -------------------------

    def get(self, guild_id: int):
        if guild_id not in self.guilds:
            self.guilds[guild_id] = GuildBrain()
        return self.guilds[guild_id]

    def path(self, guild_id: int):
        return f"data/markov_{guild_id}.json.gz"

    # -------------------------
    # SAVE / LOAD (COMPRESSED)
    # -------------------------

    def save(self, guild_id: int):
        brain = self.get(guild_id)

        data = {
            "model": brain.model.to_dict(),
            "traits": brain.traits
        }

        with gzip.open(self.path(guild_id), "wb") as f:
            f.write(json.dumps(data).encode("utf-8"))

    def load(self, guild_id: int):
        path = self.path(guild_id)

        if not os.path.exists(path):
            return

        with gzip.open(path, "rb") as f:
            data = json.loads(f.read().decode("utf-8"))

        brain = self.get(guild_id)
        brain.model = MarkovChain.from_dict(data["model"])
        brain.traits = data.get("traits", brain.traits)

    async def load_all(self):
        await self.bot.wait_until_ready()

        for g in self.bot.guilds:
            self.load(g.id)

    # -------------------------
    # MESSAGE HANDLING
    # -------------------------

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        brain = self.get(message.guild.id)

        brain.engagement["messages"] += 1

        if message.content:
            brain.model.train(message.content)

        # small behavioral drift from activity
        brain.traits["talkativeness"] += 0.0005

        self.save(message.guild.id)

        await self.maybe_reply(message, brain)

    # -------------------------
    # GENERATION
    # -------------------------

    def generate(self, brain: GuildBrain):
        text = brain.model.generate()

        chaos = brain.traits["chaos"]
        coherence = brain.traits["coherence"]

        # chaos noise injection
        if random.random() < chaos * 0.25:
            text += random.choice([" lol", " ...", " ??", ""])

        # coherence suppression
        if coherence < 0.25:
            text = text.split(".")[0]

        return text

    # -------------------------
    # TRIGGERED REPLIES
    # -------------------------

    async def maybe_reply(self, message, brain: GuildBrain):
        content = message.content.lower()

        chance = 0.03 + brain.traits["talkativeness"]

        if self.bot.user in message.mentions:
            chance = 0.9
            brain.engagement["mentions"] += 1

        if any(k in content for k in ["bot", "hello", "hey", "what", "why"]):
            chance += 0.1

        if random.random() < chance:
            brain.engagement["replies"] += 1
            await message.channel.send(self.generate(brain))

    # -------------------------
    # RANDOM CHATTER LOOP
    # -------------------------

    async def random_chatter_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(120, 420))

            for guild in self.bot.guilds:
                brain = self.get(guild.id)

                brain.drift()
                brain.model.decay()  # 👈 NEW CORE FEATURE

                # feedback normalization
                if brain.engagement["messages"] > 0:
                    ratio = brain.engagement["replies"] / brain.engagement["messages"]

                    brain.traits["talkativeness"] *= (0.9 + ratio * 0.2)

                    brain.engagement = {
                        "messages": 0,
                        "replies": 0,
                        "mentions": 0
                    }

                if random.random() > brain.traits["talkativeness"]:
                    continue

                channels = [
                    c for c in guild.text_channels
                    if c.permissions_for(guild.me).send_messages
                ]

                if not channels:
                    continue

                channel = random.choice(channels)

                try:
                    await channel.send(self.generate(brain))
                except:
                    pass

    # -------------------------
    # DREAM LOOP
    # -------------------------

    async def dream_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(300, 900))

            for guild in self.bot.guilds:
                brain = self.get(guild.id)

                # internal self-training
                for _ in range(random.randint(2, 5)):
                    text = brain.model.generate()
                    brain.model.train(text)

                # subconscious drift
                brain.traits["chaos"] += random.uniform(-0.02, 0.02)
                brain.traits["coherence"] += random.uniform(-0.01, 0.01)

                brain.traits["chaos"] = max(0, min(1, brain.traits["chaos"]))
                brain.traits["coherence"] = max(0, min(1, brain.traits["coherence"]))

    # -------------------------
    # AUTOSAVE LOOP
    # -------------------------

    async def autosave_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(60)

            for gid in list(self.guilds.keys()):
                try:
                    self.save(gid)
                except:
                    pass

    # -------------------------
    # COMMANDS
    # -------------------------

    @commands.command()
    async def markov(self, ctx):
        brain = self.get(ctx.guild.id)
        await ctx.send(self.generate(brain))

    @commands.command()
    async def brain(self, ctx):
        brain = self.get(ctx.guild.id)
        await ctx.send(str(brain.traits))

    # -------------------------
    # CLEANUP
    # -------------------------

    def cog_unload(self):
        for gid in self.guilds:
            self.save(gid)

        self.autosave_task.cancel()
        self.chatter_task.cancel()
        self.dream_task.cancel()


async def setup(bot):
    await bot.add_cog(MarkovCog(bot))