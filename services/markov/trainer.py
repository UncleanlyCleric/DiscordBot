from collections import defaultdict
import random

from core.database import db


class MarkovTrainer:
    """
    Builds word transition map from DB messages.
    """

    async def build_chain(self, guild_id: int):
        rows = await db.fetchall(
            """
            SELECT message
            FROM markov_messages
            WHERE guild_id = ?
            """,
            (guild_id,)
        )

        chain = defaultdict(list)

        for row in rows:
            words = row["message"].split()

            if len(words) < 2:
                continue

            for i in range(len(words) - 1):
                chain[words[i]].append(words[i + 1])

        return chain


markov_trainer = MarkovTrainer()