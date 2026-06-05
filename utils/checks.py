import discord
from utils.config import get as get_cfg


def is_dj():
    """
    DJ check that uses per-guild config instead of hardcoded role names.
    Works with discord.py commands check decorator.
    """

    async def predicate(ctx):
        if not ctx.guild:
            return False

        # Admins always allowed
        if ctx.author.guild_permissions.administrator:
            return True

        cfg = get_cfg(ctx.guild.id)
        role_id = cfg.get("dj_role_id")

        # No DJ role configured
        if not role_id:
            return False

        # Ensure we have a Member object (not DM context)
        if not isinstance(ctx.author, discord.Member):
            return False

        # Check role membership
        return any(role.id == role_id for role in ctx.author.roles)

    return discord.app_commands.check(predicate)