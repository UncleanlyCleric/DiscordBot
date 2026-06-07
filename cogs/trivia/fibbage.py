import random
import discord


class FibbageEngine:
    def __init__(self):
        pass

    async def run_round(self, lobby, channel, question):
        lobby.submissions = {}
        lobby.votes = {}

        await channel.send(
            f"🧠 **FIBBAGE ROUND**\n{question['question']}\n\n"
            "Use `/fib_submit <answer>`"
        )

        await self.wait(20)

        choices = self.build_choices(lobby, question)
        lobby.current_choices = choices

        await self.voting_phase(lobby, channel, question, choices)

    async def wait(self, seconds):
        import asyncio
        await asyncio.sleep(seconds)

    def build_choices(self, lobby, question):
        choices = [question["choices"][question["answer"]]]

        for fake in lobby.submissions.values():
            choices.append(fake)

        random.shuffle(choices)
        return choices

    async def voting_phase(self, lobby, channel, question, choices):
        view = FibbageView(lobby, question, choices)

        embed = discord.Embed(
            title="🗳️ Vote for the real answer",
            description=question["question"]
        )

        for i, c in enumerate(choices):
            embed.add_field(name=str(i + 1), value=c, inline=False)

        await channel.send(embed=embed, view=view)

        await view.wait()

        await self.score(lobby, channel, question, choices)

    async def score(self, lobby, channel, question, choices):
        correct = question["choices"][question["answer"]]

        await channel.send(f"📢 Correct: **{correct}**")

        # correct guesses
        for uid, vote in lobby.votes.items():
            if choices[vote] == correct:
                lobby.scores[uid] = lobby.scores.get(uid, 0) + 1000

        # deception points
        for uid, fake in lobby.submissions.items():
            fooled = sum(
                1 for v in lobby.votes.values()
                if choices[v] == fake
            )
            lobby.scores[uid] = lobby.scores.get(uid, 0) + fooled * 500


class FibbageView(discord.ui.View):
    def __init__(self, lobby, question, choices):
        super().__init__(timeout=20)
        self.lobby = lobby
        self.question = question
        self.choices = choices

        for i, c in enumerate(choices):
            self.add_item(FibbageButton(i))


class FibbageButton(discord.ui.Button):
    def __init__(self, idx):
        super().__init__(label=str(idx + 1), style=discord.ButtonStyle.primary)
        self.idx = idx

    async def callback(self, interaction: discord.Interaction):
        lobby = self.view.lobby

        if interaction.user.id not in lobby.players:
            return await interaction.response.send_message("Not in game.", ephemeral=True)

        lobby.votes[interaction.user.id] = self.idx

        await interaction.response.send_message("Locked in!", ephemeral=True)