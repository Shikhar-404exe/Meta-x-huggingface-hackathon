from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, Dict, cast

from .env import AttentionEconomyEnv
from .models import FeedAction, Observation

MIN_SCORE = 0.01
MAX_SCORE = 0.99
AgentFn = Callable[[Observation], FeedAction | Dict[str, Any]]


def safe_score(score: float) -> float:
    # Keep all grader outputs strictly inside (0, 1).
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
    # Accept grade_x(seed) style invocations from external validator harnesses.
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


def _diversity_from_state(state: Dict[str, Any]) -> float:
    categories = [h.get("category") for h in state["history"] if h.get("category")]
    if not categories:
        return 0.0
    return len(set(categories)) / len(categories)


def run_agent_on_task(
    agent_fn: object | None,
    task_id: str,
    seed: Any = 42,
) -> Dict[str, Any]:
    runner, resolved_seed = _resolve_runner_and_seed(agent_fn, seed)
    env = AttentionEconomyEnv(task_id=task_id, seed=resolved_seed)
    obs = env.reset(task_id=task_id, seed=resolved_seed)

    while True:
        action = runner(obs)
        if not isinstance(action, FeedAction):
            action = FeedAction(**action)

        obs, _, done, _ = env.step(action)
        if done:
            break

    state = env.state()
    metrics = state["metrics"]
    diversity = _diversity_from_state(state)

    return {
        "task_id": task_id,
        "metrics": metrics,
        "diversity": diversity,
        "unsafe_events": state["unsafe_events"],
        "loop_penalties": state["loop_penalties"],
        "steps": state["step"],
    }


def grade_task_easy(
    agent_fn: object | None = None,
    seed: Any = 42,
) -> float:
    result = run_agent_on_task(agent_fn, "easy", seed=seed)
    m = result["metrics"]
    penalties = 0.08 * result["unsafe_events"] + 0.04 * result["loop_penalties"]
    score = 0.60 * m["engagement"] + 0.40 * (1.0 - m["addiction_level"]) - penalties
    return round(safe_score(score), 4)


def grade_task_medium(
    agent_fn: object | None = None,
    seed: Any = 42,
) -> float:
    result = run_agent_on_task(agent_fn, "medium", seed=seed)
    m = result["metrics"]
    penalties = 0.08 * result["unsafe_events"] + 0.05 * result["loop_penalties"]
    score = 0.45 * m["engagement"] + 0.45 * m["productivity"] + 0.10 * result["diversity"] - penalties
    return round(safe_score(score), 4)


def grade_task_hard(
    agent_fn: object | None = None,
    seed: Any = 42,
) -> float:
    result = run_agent_on_task(agent_fn, "hard", seed=seed)
    m = result["metrics"]
    penalties = 0.12 * result["unsafe_events"] + 0.05 * result["loop_penalties"]
    score = 0.30 * m["engagement"] + 0.25 * m["productivity"] + 0.45 * m["wellbeing"] - penalties
    return round(safe_score(score), 4)


# Aliases used by validators that expect short grader names.
grade_easy = grade_task_easy
grade_medium = grade_task_medium
grade_hard = grade_task_hard


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

# Compatibility aliases for validators that expect different exported names.
TASK_GRADERS = GRADERS


def get_graders() -> Mapping[str, Callable[..., float]]:
    return GRADERS


def grade_all(
    agent_fn: object | None = None,
    seed: Any = 42,
) -> Dict[str, float]:
    scores = {task_id: grader(agent_fn, seed=seed) for task_id, grader in GRADERS.items()}
    scores["overall"] = round(safe_score(sum(scores.values()) / len(GRADERS)), 4)
    return scores
