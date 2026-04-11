from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

import graders as root_graders


class EasyGrader:
    def grade(self, *args: Any, **kwargs: Any) -> float:
        return float(root_graders.grade_easy(*args, **kwargs))


class MediumGrader:
    def grade(self, *args: Any, **kwargs: Any) -> float:
        return float(root_graders.grade_medium(*args, **kwargs))


class HardGrader:
    def grade(self, *args: Any, **kwargs: Any) -> float:
        return float(root_graders.grade_hard(*args, **kwargs))


def grade_easy(*args: Any, **kwargs: Any) -> float:
    return float(root_graders.grade_easy(*args, **kwargs))


def grade_medium(*args: Any, **kwargs: Any) -> float:
    return float(root_graders.grade_medium(*args, **kwargs))


def grade_hard(*args: Any, **kwargs: Any) -> float:
    return float(root_graders.grade_hard(*args, **kwargs))


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

TASK_GRADERS = GRADERS


def get_graders() -> Mapping[str, Callable[..., float]]:
    return GRADERS


def grade_all(*args: Any, **kwargs: Any) -> dict[str, float]:
    scores = root_graders.grade_all(*args, **kwargs)
    return {k: float(v) for k, v in scores.items()}
