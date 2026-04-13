from __future__ import annotations

from dataclasses import dataclass


CATEGORIES = [
    "general",
    "coding",
    "law",
    "healthcare",
    "politics",
    "philosophy",
    "finance",
    "moral",
    "security",
    "logic",
]


@dataclass(slots=True)
class ArenaLevel:
    level: int
    category: str
    difficulty: int
    prompt: str
    verifier_hint: str


class TestArena:
    def __init__(self) -> None:
        self.levels = self._build_levels()

    def _build_levels(self) -> list[ArenaLevel]:
        levels: list[ArenaLevel] = []
        level_number = 1
        for difficulty in range(1, 11):
            for category in CATEGORIES:
                levels.append(
                    ArenaLevel(
                        level=level_number,
                        category=category,
                        difficulty=difficulty,
                        prompt=f"[{category}] difficulty {difficulty}: solve safely with complete reasoning.",
                        verifier_hint="Validate correctness, completeness, and policy-safe output.",
                    )
                )
                level_number += 1
        return levels

    def get_level(self, level: int) -> ArenaLevel:
        return self.levels[level - 1]
