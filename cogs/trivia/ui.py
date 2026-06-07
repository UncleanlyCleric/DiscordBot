import discord
import time

class AnswerView(discord.ui.View):
    def __init__(self, game, question, modifier):
        super().__init__(timeout=15)
        self.game = game
        self.question = question
        self.start = time.time()
        self.modifier = modifier

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def a(self, interaction, button):
        await self.handle(interaction, 0)

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def b(self, interaction, button):
        await self.handle(interaction, 1)

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def c(self, interaction, button):
        await self.handle(interaction, 2)

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def d(self, interaction, button):
        await self.handle(interaction, 3)

    async def handle(self, interaction, index):
        uid = interaction.user.id

        if uid not in self.game.players:
            return await interaction.response.send_message("Not in game.", ephemeral=True)

        correct = self.question["answer"]

        base = 100 if index == correct else -25

        from .modifiers import apply_score
        final = apply_score(base, index == correct, self.modifier)

        self.game.scores[uid] = self.game.scores.get(uid, 0) + final

        await interaction.response.send_message(
            f"{'✅ Correct' if index == correct else '❌ Wrong'} ({final})",
            ephemeral=True
        )