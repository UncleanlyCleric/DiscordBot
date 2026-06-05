import discord
from discord.ext import commands


class CoreLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info(f"Logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.logger.info(
            f"CMD: {ctx.author} used {ctx.command} in {ctx.guild}"
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        self.bot.logger.error(
            f"ERROR in {ctx.command}: {error}"
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.logger.info(f"Joined guild: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.bot.logger.info(f"Left guild: {guild.name} ({guild.id})")


async def setup(bot):
    await bot.add_cog(CoreLogging(bot))