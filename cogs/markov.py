import os
import json
import gzip
import random
import asyncio
import discord
from discord.ext import commands

from markov_core import MarkovChain
from utils.config import get as get_cfg


# -----------------------------
# GUILD STATE
# -----------------------------

class GuildBrain:
    def __init__(self):
        self.model = MarkovChain()

        self.traits = {
            "chaos": 0.3,
            "coherence": 0.6,
            "talkativeness": 0.4
        }

        self.engagement = {
            "messages": 0,
            "replies": 0,
            "mentions": 0
        }

        self.lock = asyncio.Lock()

    def drift(self):
        for k in self.traits:
            self.traits[k] += random.uniform(-0.01, 0.01)
            self.traits[k] = max(0.0, min(1.0, self.traits[k]))


# -----------------------------
# MARKOV COG
# -----------------------------

class MarkovCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds: dict[int, GuildBrain] = {}

        os.makedirs("data", exist_ok=True)

        self.bot.loop.create_task(self._startup())

        self.autosave_task = self.bot.loop.create_task(self.autosave_loop())
        self.chatter_task = self.bot.loop.create_task(self.random_chatter_loop())
        self.dream_task = self.bot.loop.create_task(self.dream_loop())

    # -------------------------
    # STARTUP
    # -------------------------

    async def _startup(self):
        await self.bot.wait_until_ready()
        await self.load_all()

    # -------------------------
    # STATE
    # -------------------------

    def get(self, guild_id: int):
        if guild_id not in self.guilds:
            self.guilds[guild_id] = GuildBrain()
        return self.guilds[guild_id]

    def path(self, guild_id: int):
        return f"data/markov_{guild_id}.json.gz"

    # -------------------------
    # SAVE / LOAD
    # -------------------------

    async def save(self, guild_id: int):
        brain = self.get(guild_id)

        async with brain.lock:
            cfg = get_cfg(guild_id)

            data = {
                "model": brain.model.to_dict(),
                "traits": brain.traits,
                "engagement": brain.engagement,
                "channel_id": cfg["markov_channel_id"],
                "training_enabled": cfg["markov_training"]
            }

            with gzip.open(self.path(guild_id), "wb") as f:
                f.write(json.dumps(data).encode("utf-8"))

    def load(self, guild_id: int):
        path = self.path(guild_id)

        if not os.path.exists(path):
            return

        try:
            with gzip.open(path, "rb") as f:
                data = json.loads(f.read().decode("utf-8"))

            brain = self.get(guild_id)
            brain.model = MarkovChain.from_dict(data["model"])
            brain.traits = data.get("traits", brain.traits)
            brain.engagement = data.get("engagement", brain.engagement)

        except Exception as e:
            print(f"[Markov Load Error] {guild_id}: {e}")

    async def load_all(self):
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
        cfg = get_cfg(message.guild.id)

        # -------------------------
        # CONFIG GATES
        # -------------------------

        if not cfg["markov_training"]:
            return

        if cfg["markov_channel_id"] and message.channel.id != cfg["markov_channel_id"]:
            return

        # -------------------------
        # TRAINING
        # -------------------------

        brain.engagement["messages"] += 1

        if message.content:
            async with brain.lock:
                brain.model.train(message.content)

        brain.traits["talkativeness"] += 0.0005

        await self.maybe_reply(message, brain, cfg)

    # -------------------------
    # GENERATION
    # -------------------------

    def generate(self, brain: GuildBrain):
        text = brain.model.generate()

        if random.random() < brain.traits["chaos"] * 0.25:
            text += random.choice([" lol", " ...", " ??", ""])

        if brain.traits["coherence"] < 0.25:
            text = text.split(".")[0]

        return text

    # -------------------------
    # REPLY LOGIC
    # -------------------------

    async def maybe_reply(self, message, brain: GuildBrain, cfg):
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
    # CHATTER LOOP
    # -------------------------

    async def random_chatter_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(120, 420))

            for guild in self.bot.guilds:
                brain = self.get(guild.id)

                brain.drift()
                brain.model.decay()

                if brain.engagement["messages"] > 0:
                    ratio = brain.engagement["replies"] / brain.engagement["messages"]
                    brain.traits["talkativeness"] *= (0.9 + ratio * 0.2)

                brain.engagement = {
                    "messages": 0,
                    "replies": 0,
                    "mentions": 0
                }

                cfg = get_cfg(guild.id)

                if not cfg["markov_training"]:
                    continue

                if cfg["markov_channel_id"]:
                    continue  # avoids random spam outside channel lock

                if random.random() > brain.traits["talkativeness"]:
                    continue

                try:
                    channels = [
                        c for c in guild.text_channels
                        if c.permissions_for(guild.me).send_messages
                    ]

                    if not channels:
                        continue

                    await random.choice(channels).send(self.generate(brain))

                except Exception as e:
                    print(f"[Chatter Error] {guild.id}: {e}")

    # -------------------------
    # DREAM LOOP
    # -------------------------

    async def dream_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(300, 900))

            for guild in self.bot.guilds:
                brain = self.get(guild.id)

                for _ in range(random.randint(2, 5)):
                    text = brain.model.generate()
                    brain.model.train(text)

    # -------------------------
    # AUTOSAVE LOOP
    # -------------------------

    async def autosave_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            await asyncio.sleep(60)

            for gid in list(self.guilds.keys()):
                try:
                    await self.save(gid)
                except Exception as e:
                    print(f"[Markov Save Error] {gid}: {e}")

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
            asyncio.create_task(self.save(gid))

        self.autosave_task.cancel()
        self.chatter_task.cancel()
        self.dream_task.cancel()


async def setup(bot):
    await bot.add_cog(MarkovCog(bot))