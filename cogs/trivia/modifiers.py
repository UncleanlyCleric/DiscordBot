import random

MODIFIERS = [
    "normal",
    "double_points",
    "reverse_scoring"
]


def pick_modifier():
    return random.choice(MODIFIERS)


def apply(score, correct: bool, mod: str):
    if mod == "double_points":
        return score * 2

    if mod == "reverse_scoring":
        return 0 if correct else 100

    return score