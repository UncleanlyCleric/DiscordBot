import random
import asyncio

import discord

from .hosts import HOSTS, pick_host
from .modifiers import pick_modifier, apply
from .reaction_engine import HostReactionEngine
from .fibbage import FibbageEngine


class TriviaEngine:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        # engines stored per active game channel
        self.reaction_engines = {}

        # fibbage engine (shared)
        self.fibbage = FibbageEngine()

    # -----------------------------
    # MAIN GAME ENTRY
    # -----------------------------
    async def run(self, lobby, channel, questions):
        lobby.active = True
        lobby.in_lobby = False

        # assign flavor systems
        lobby.host_personality = pick_host()
        lobby.modifier = pick_modifier()

        self.reaction_engines[lobby.channel_id] = HostReactionEngine(
            lobby.host_personality
        )

        reaction = self.reaction_engines[lobby.channel_id]

        await channel.send(
            f"🎤 Host: **{lobby.host_personality}**\n"
            f"💣 Modifier: **{lobby.modifier}**\n\n"
            f"{reaction.react('correct')}"
        )

        # -------------------------
        # FIBBAGE MODE
        # -------------------------
        if lobby.mode == "fibbage":
            for q in questions:
                await self.fibbage.run_round(lobby, channel, q, reaction)

            await self.end(lobby, channel)
            return

        # -------------------------
        # CLASSIC MODE
        # -------------------------
        for q in questions:
            await self.classic_round(lobby, channel, q, reaction)

        await self.end(lobby, channel)

    # -----------------------------
    # CLASSIC ROUND
    # -----------------------------
    async def classic_round(self, lobby, channel, q, reaction):
        lobby.reset_round_state()

        embed = discord.Embed(
            title="🎲 Trivia Question",
            description=q["question"],
            color=discord.Color.blurple()
        )

        for i, c in enumerate(q["choices"]):
            embed.add_field(name=chr(65 + i), value=c, inline=False)

        msg = await channel.send(embed=embed)

        # simple wait window (buttons handled elsewhere)
        await asyncio.sleep(10)

        correct = q["answer"]
        correct_text = q["choices"][correct]

        await channel.send(f"📢 Correct answer: **{correct_text}**")

        # host reaction (generic round end flavor)
        await channel.send(reaction.react("correct"))

    # -----------------------------
    # END GAME
    # -----------------------------
    async def end(self, lobby, channel):
        scores = sorted(lobby.scores.items(), key=lambda x: x[1], reverse=True)

        lines = ["🏁 **Final Scores**"]

        for uid, score in scores:
            user = self.bot.get_user(uid)
            name = user.display_name if user else str(uid)

            lines.append(f"• {name}: **{score}**")

            self.db.add_score(uid, score)
            self.db.add_game(uid)

        # winner tracking
        if scores:
            self.db.add_win(scores[0][0])

            winner = self.bot.get_user(scores[0][0])
            if winner:
                await channel.send(
                    f"👑 Winner: {winner.mention}\n"
                    f"{self.reaction_engines[lobby.channel_id].react('correct')}"
                )

        await channel.send("\n".join(lines))

        # cleanup engine memory
        if lobby.channel_id in self.reaction_engines:
            del self.reaction_engines[lobby.channel_id]