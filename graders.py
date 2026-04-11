from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, Dict, cast

from support_env.graders import (
    grade_all as _grade_all,
    grade_task_easy as _grade_task_easy,
    grade_task_hard as _grade_task_hard,
    grade_task_medium as _grade_task_medium,
)
from support_env.models import FeedAction, Observation

MIN_SCORE = 0.1
MAX_SCORE = 0.99
AgentFn = Callable[[Observation], FeedAction | Dict[str, Any]]


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


def _resolve_runner_and_seed(
    agent_fn: object | None = None,
    seed: Any = 42,
) -> tuple[AgentFn, int]:
    # Some validators call graders as grade_x(seed) instead of grade_x(agent_fn, seed).
    # If first positional arg is not callable, treat it as seed.
    resolved_agent = agent_fn
    resolved_seed = seed

    if resolved_agent is not None and not callable(resolved_agent):
        resolved_seed = resolved_agent
        resolved_agent = None

    try:
        resolved_seed_int = int(str(resolved_seed))
    except Exception:
        resolved_seed_int = 42

    runner: AgentFn = cast(AgentFn, resolved_agent) if callable(resolved_agent) else _default_agent
    return runner, resolved_seed_int


def _resolve_compat_kwargs(
    agent_fn: object | None,
    seed: Any,
    kwargs: Dict[str, Any] | None = None,
) -> tuple[object | None, Any]:
    extra = dict(kwargs or {})

    if agent_fn is None:
        for key in ("agent", "runner", "policy", "policy_fn", "inference_fn", "fn"):
            candidate = extra.pop(key, None)
            if callable(candidate):
                agent_fn = candidate
                break

    for key in ("random_seed", "rng_seed", "episode_seed"):
        if key in extra:
            seed = extra.pop(key)
            break

    # Intentionally ignore any remaining unknown kwargs for validator compatibility.
    return agent_fn, seed


def _resolve_compat_call(
    args: tuple[Any, ...],
    *,
    agent_fn: object | None = None,
    seed: Any = 42,
    kwargs: Dict[str, Any] | None = None,
) -> tuple[object | None, Any]:
    resolved_agent = agent_fn
    resolved_seed = seed

    for arg in args:
        if callable(arg) and resolved_agent is None:
            resolved_agent = arg
            continue
        if not callable(arg):
            resolved_seed = arg

    return _resolve_compat_kwargs(resolved_agent, resolved_seed, kwargs)


def grade_easy(
    *args: Any,
    agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None,
    seed: int = 42,
    **kwargs: Any,
) -> float:
    resolved_agent, resolved_seed_input = _resolve_compat_call(args, agent_fn=agent_fn, seed=seed, kwargs=kwargs)
    runner, resolved_seed = _resolve_runner_and_seed(resolved_agent, resolved_seed_input)
    return safe_score(_grade_task_easy(runner, seed=resolved_seed))


def grade_medium(
    *args: Any,
    agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None,
    seed: int = 42,
    **kwargs: Any,
) -> float:
    resolved_agent, resolved_seed_input = _resolve_compat_call(args, agent_fn=agent_fn, seed=seed, kwargs=kwargs)
    runner, resolved_seed = _resolve_runner_and_seed(resolved_agent, resolved_seed_input)
    return safe_score(_grade_task_medium(runner, seed=resolved_seed))


def grade_hard(
    *args: Any,
    agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None,
    seed: int = 42,
    **kwargs: Any,
) -> float:
    resolved_agent, resolved_seed_input = _resolve_compat_call(args, agent_fn=agent_fn, seed=seed, kwargs=kwargs)
    runner, resolved_seed = _resolve_runner_and_seed(resolved_agent, resolved_seed_input)
    return safe_score(_grade_task_hard(runner, seed=resolved_seed))


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


def grade_all(
    *args: Any,
    agent_fn: Callable[[Observation], FeedAction | Dict[str, Any]] | None = None,
    seed: int = 42,
    **kwargs: Any,
) -> Dict[str, float]:
    resolved_agent, resolved_seed_input = _resolve_compat_call(args, agent_fn=agent_fn, seed=seed, kwargs=kwargs)
    runner, resolved_seed = _resolve_runner_and_seed(resolved_agent, resolved_seed_input)
    scores = {
        task_id: safe_score(grader(runner, seed=resolved_seed))
        for task_id, grader in GRADERS.items()
    }
    scores["overall"] = safe_score(sum(scores.values()) / len(GRADERS))
    return scores


# Retain underlying implementation import path compatibility.
BASELINE_GRADE_ALL = _grade_all
