import random
from collections import defaultdict


class MarkovCore:
    """
    SAFE MARKOV TEXT ENGINE

    RULES:
    - no file IO at import time
    - no DB dependency
    - no bot dependency
    - pure in-memory model
    """

    def __init__(self):
        self.model = defaultdict(list)
        self.built = False

    # ---------------------------
    # Training
    # ---------------------------

    def train(self, text: str):
        words = text.split()

        if len(words) < 2:
            return

        for i in range(len(words) - 1):
            self.model[words[i]].append(words[i + 1])

        self.built = True

    # ---------------------------
    # Generation
    # ---------------------------

    def generate(self, start_word: str = None, length: int = 20):
        if not self.model:
            return ""

        if not start_word or start_word not in self.model:
            start_word = random.choice(list(self.model.keys()))

        word = start_word
        output = [word]

        for _ in range(length - 1):
            next_words = self.model.get(word)

            if not next_words:
                break

            word = random.choice(next_words)
            output.append(word)

        return " ".join(output)

    # ---------------------------
    # Persistence Support
    # ---------------------------

    def to_dict(self):
        return {
            "model": dict(self.model),
            "built": self.built
        }

    @classmethod
    def from_dict(cls, data):
        obj = cls()

        model = data.get("model", {})

        for key, values in model.items():
            obj.model[key] = list(values)

        obj.built = data.get("built", bool(obj.model))
        return obj

    # ---------------------------
    # Compatibility Methods
    # ---------------------------

    def decay(self):
        """
        Compatibility stub for older Markov cog.
        Safe no-op.
        """
        pass

    # ---------------------------
    # Reset / Utility
    # ---------------------------

    def clear(self):
        self.model.clear()
        self.built = False


# --------------------------------
# Backward Compatibility Alias
# --------------------------------

MarkovChain = MarkovCore


# --------------------------------
# Singleton
# --------------------------------

markov_core = MarkovCore()