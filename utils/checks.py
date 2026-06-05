import discord

DJ_ROLE_NAME = "DJ"

def is_dj():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True

        role = discord.utils.get(ctx.author.roles, name=DJ_ROLE_NAME)
        return role is not None

    return discord.app_commands.check(predicate)