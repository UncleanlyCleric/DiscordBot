import discord
from discord import app_commands
from discord.ext import commands

import random
import time

from core.cog_base import BaseCog
from services.markov.service import markov_service
from services.markov.trainer import markov_trainer
from services.markov.generator import markov_generator


class MarkovCog(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)

        # in-memory cooldown tracking
        self.last_spoke = {}
        self.user_cooldown = {}

    # -------------------------
    # MESSAGE LISTENER
    # -------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        guild_id = message.guild.id
        channel_id = message.channel.id

        content = message.content.strip()

        # 1. ingest every message (if allowed channel OR we want global learning)
        if await markov_service.is_channel_allowed(guild_id, channel_id):
            await markov_service.ingest(guild_id, channel_id, content)

        # 2. check if bot should even consider speaking
        if not await markov_service.is_enabled(guild_id):
            return

        # 3. cooldown (guild-level)
        now = time.time()
        if guild_id in self.last_spoke:
            if now - self.last_spoke[guild_id] < 20:
                return

        # 4. probability base
        chance = 0.005  # 0.5%

        # 5. mention / name bias
        bot_user = self.bot.user
        if bot_user:
            if bot_user.mentioned_in(message):
                chance += 0.12

            if bot_user.name.lower() in content.lower():
                chance += 0.06

        # 6. user spam protection
        uid = message.author.id
        if uid in self.user_cooldown:
            if now - self.user_cooldown[uid] < 60:
                return

        # 7. roll
        if random.random() > chance:
            return

        # 8. generate response
        chain = await markov_trainer.build_chain(guild_id)
        response = markov_generator.generate(chain)

        if not response:
            return

        await message.channel.send(response)

        # update cooldowns
        self.last_spoke[guild_id] = now
        self.user_cooldown[uid] = now

    # -------------------------
    # ENABLE
    # -------------------------

    @app_commands.command(
        name="markov_enable",
        description="Enable Markov chat in this server."
    )
    async def enable(self, interaction: discord.Interaction):
        await self.ensure_guild(interaction.guild_id)

        await self.db.execute(
            """
            UPDATE guild_settings
            SET markov_enabled = 1
            WHERE guild_id = ?
            """,
            (interaction.guild_id,)
        )

        await self.send_success(interaction, "Markov enabled.")

    # -------------------------
    # DISABLE (NEW)
    # -------------------------

    @app_commands.command(
        name="markov_disable",
        description="Disable Markov chat in this server."
    )
    async def disable(self, interaction: discord.Interaction):
        await self.ensure_guild(interaction.guild_id)

        await self.db.execute(
            """
            UPDATE guild_settings
            SET markov_enabled = 0
            WHERE guild_id = ?
            """,
            (interaction.guild_id,)
        )

        await self.send_success(interaction, "Markov disabled.")

    # -------------------------
    # CHANNEL ADD
    # -------------------------

    @app_commands.command(
        name="markov_channel_add",
        description="Allow a channel for Markov training."
    )
    async def channel_add(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.ensure_guild(interaction.guild_id)

        await markov_service.add_channel(interaction.guild_id, channel.id)

        await self.send_success(
            interaction,
            f"Markov enabled in {channel.mention}"
        )

    # -------------------------
    # CHANNEL REMOVE
    # -------------------------

    @app_commands.command(
        name="markov_channel_remove",
        description="Remove a Markov training channel."
    )
    async def channel_remove(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.ensure_guild(interaction.guild_id)

        await markov_service.remove_channel(interaction.guild_id, channel.id)

        await self.send_success(
            interaction,
            f"Markov disabled in {channel.mention}"
        )

    # -------------------------
    # MANUAL SPEAK (DEBUG / FUN)
    # -------------------------

    @app_commands.command(
        name="markov_speak",
        description="Force Markov to generate a message."
    )
    async def speak(self, interaction: discord.Interaction):
        await self.ensure_guild(interaction.guild_id)

        chain = await markov_trainer.build_chain(interaction.guild_id)
        response = markov_generator.generate(chain)

        if not response:
            await self.send_error(interaction, "No data to generate from.")
            return

        await interaction.response.send_message(response)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarkovCog(bot))