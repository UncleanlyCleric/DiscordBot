import random
from typing import Dict, List


class MarkovGenerator:
    """
    Generates sentences from a word chain.
    """

    def generate(
        self,
        chain: Dict[str, List[str]],
        min_words: int = 5,
        max_words: int = 20
    ) -> str:

        if not chain:
            return ""

        word = random.choice(list(chain.keys()))
        output = [word]

        for _ in range(random.randint(min_words, max_words)):
            if word not in chain:
                break

            next_words = chain[word]

            if not next_words:
                break

            word = random.choice(next_words)
            output.append(word)

        return " ".join(output)


markov_generator = MarkovGenerator()