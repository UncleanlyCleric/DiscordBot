import random
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional


DICE_PATTERN = re.compile(
    r"(?P<count>\d*)d(?P<sides>\d+)"
    r"(?:(?P<modifier>[+-]\d+))?"
    r"(?:(?P<keep>k[hl]\d+))?"
)


@dataclass
class RollResult:
    rolls: List[int]
    kept: List[int]
    total: int
    expression: str


class DiceRoller:
    """
    Supports:
    - NdM (e.g. 4d6)
    - modifiers (+3, -1)
    - keep highest/lowest (kh3, kl2)
    """

    def roll_single(self, sides: int) -> int:
        return random.randint(1, sides)

    def parse(self, expression: str) -> RollResult:
        match = DICE_PATTERN.fullmatch(expression.replace(" ", ""))

        if not match:
            raise ValueError("Invalid dice expression")

        count = int(match.group("count") or 1)
        sides = int(match.group("sides"))
        modifier = match.group("modifier")
        keep = match.group("keep")

        rolls = [self.roll_single(sides) for _ in range(count)]

        kept = rolls.copy()

        # -------------------------
        # KEEP HIGHEST / LOWEST
        # -------------------------
        if keep:
            k_type = keep[1]
            k_value = int(keep[2:])

            if k_type == "h":
                kept = sorted(rolls, reverse=True)[:k_value]
            else:
                kept = sorted(rolls)[:k_value]

        total = sum(kept)

        # -------------------------
        # MODIFIER
        # -------------------------
        if modifier:
            total += int(modifier)

        return RollResult(
            rolls=rolls,
            kept=kept,
            total=total,
            expression=expression
        )

    def advantage(self, sides: int = 20) -> RollResult:
        rolls = [self.roll_single(sides), self.roll_single(sides)]
        kept = [max(rolls)]
        return RollResult(
            rolls=rolls,
            kept=kept,
            total=kept[0],
            expression="advantage"
        )

    def disadvantage(self, sides: int = 20) -> RollResult:
        rolls = [self.roll_single(sides), self.roll_single(sides)]
        kept = [min(rolls)]
        return RollResult(
            rolls=rolls,
            kept=kept,
            total=kept[0],
            expression="disadvantage"
        )


dice_roller = DiceRoller()