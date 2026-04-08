from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, Dict

from support_env.graders import (
    grade_all as _grade_all,
    grade_task_easy as _grade_task_easy,
    grade_task_hard as _grade_task_hard,
    grade_task_medium as _grade_task_medium,
)
from support_env.models import FeedAction, Observation

EPSILON = 1e-3


def _strict_score(value: float) -> float:
    return max(EPSILON, min(1.0 - EPSILON, float(value)))


def grade_easy(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]], seed: int = 42) -> float:
    return _strict_score(_grade_task_easy(agent_fn, seed=seed))


def grade_medium(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]], seed: int = 42) -> float:
    return _strict_score(_grade_task_medium(agent_fn, seed=seed))


def grade_hard(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]], seed: int = 42) -> float:
    return _strict_score(_grade_task_hard(agent_fn, seed=seed))


# Aliases used by some validators.
grade_task_easy = grade_easy
grade_task_medium = grade_medium
grade_task_hard = grade_hard

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

# Alternate name often used in grading harnesses.
TASK_GRADERS = GRADERS


def get_graders() -> Mapping[str, Callable[[Callable[[Observation], FeedAction | Dict[str, Any]], int], float]]:
    return GRADERS


def grade_all(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]], seed: int = 42) -> Dict[str, float]:
    scores = {
        task_id: _strict_score(grader(agent_fn, seed=seed))
        for task_id, grader in GRADERS.items()
    }
    scores["overall"] = _strict_score(sum(scores.values()) / len(GRADERS))
    return scores


# Retain underlying implementation import path compatibility.
BASELINE_GRADE_ALL = _grade_all
