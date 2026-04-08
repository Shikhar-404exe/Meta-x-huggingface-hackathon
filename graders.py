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

MIN_SCORE = 0.01
MAX_SCORE = 0.99


def safe_score(score: float) -> float:
    return max(MIN_SCORE, min(MAX_SCORE, float(score)))


def _default_agent(obs: Observation) -> FeedAction | Dict[str, Any]:
    if obs.fatigue > 0.75:
        return FeedAction(action_type="suggest_break", break_minutes=7)

    if obs.addiction_level > 0.70:
        return FeedAction(action_type="reorder_feed", strategy="prioritize_wellbeing")

    safe_items = [x for x in obs.feed_items if x.category != "toxic"]
    target = safe_items[0] if safe_items else obs.feed_items[0]
    return FeedAction(action_type="recommend_item", item_id=target.id, rationale="default grader policy")


def grade_easy(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None, seed: int = 42) -> float:
    runner = agent_fn or _default_agent
    return safe_score(_grade_task_easy(runner, seed=seed))


def grade_medium(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None, seed: int = 42) -> float:
    runner = agent_fn or _default_agent
    return safe_score(_grade_task_medium(runner, seed=seed))


def grade_hard(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None, seed: int = 42) -> float:
    runner = agent_fn or _default_agent
    return safe_score(_grade_task_hard(runner, seed=seed))


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


def get_graders() -> Mapping[str, Callable[..., float]]:
    return GRADERS


def grade_all(agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None, seed: int = 42) -> Dict[str, float]:
    runner = agent_fn or _default_agent
    scores = {
        task_id: safe_score(grader(runner, seed=seed))
        for task_id, grader in GRADERS.items()
    }
    scores["overall"] = safe_score(sum(scores.values()) / len(GRADERS))
    return scores


# Retain underlying implementation import path compatibility.
BASELINE_GRADE_ALL = _grade_all
