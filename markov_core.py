import random
import re
from collections import defaultdict


# -----------------------------
# TOKENIZATION
# -----------------------------

def tokenize(text: str):
    return re.findall(r"\b\w+\b|[.!?]", text.lower())


# -----------------------------
# MARKOV CHAIN (TRIGRAM + WEIGHTS)
# -----------------------------

class MarkovChain:
    def __init__(self):
        # trigram -> {next_word: weight}
        self.chain = defaultdict(lambda: defaultdict(float))

        # starting points (for sentence initiation)
        self.starts = []

    # -----------------------------
    # TRAINING
    # -----------------------------

    def train(self, text: str):
        words = tokenize(text)

        if len(words) < 4:
            return

        # store start state
        self.starts.append((words[0], words[1], words[2]))

        # build trigram transitions
        for i in range(len(words) - 3):
            key = (words[i], words[i + 1], words[i + 2])
            nxt = words[i + 3]

            self.chain[key][nxt] += 1.0

    # -----------------------------
    # GENERATION
    # -----------------------------

    def generate(self, max_words=30):
        if not self.chain or not self.starts:
            return "..."

        w1, w2, w3 = random.choice(self.starts)
        output = [w1, w2, w3]

        for _ in range(max_words):
            key = (output[-3], output[-2], output[-1])

            options = self.chain.get(key)
            if not options:
                break

            words = list(options.keys())
            weights = list(options.values())

            nxt = random.choices(words, weights=weights, k=1)[0]
            output.append(nxt)

            if nxt in ".!?":
                break

        return " ".join(output).capitalize()

    # -----------------------------
    # MEMORY DECAY
    # -----------------------------

    def decay(self, rate: float = 0.995, floor: float = 0.05):
        """
        Gradually reduces memory strength over time.
        Prevents infinite growth + removes unused language.
        """

        for key in list(self.chain.keys()):
            inner = self.chain[key]

            for word in list(inner.keys()):
                inner[word] *= rate

                if inner[word] < floor:
                    del inner[word]

            if not inner:
                del self.chain[key]

        # optional: slowly decay start memory too
        if len(self.starts) > 5000:
            self.starts = self.starts[-5000:]

    # -----------------------------
    # SERIALIZATION
    # -----------------------------

    def to_dict(self):
        return {
            "starts": self.starts,
            "chain": {
                str(k): dict(v)
                for k, v in self.chain.items()
            }
        }

    @classmethod
    def from_dict(cls, data):
        obj = cls()

        obj.starts = [
            tuple(x) for x in data.get("starts", [])
        ]

        for k, v in data.get("chain", {}).items():
            obj.chain[tuple(eval(k))] = defaultdict(
                float,
                v
            )

        return obj