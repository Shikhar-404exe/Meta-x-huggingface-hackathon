from __future__ import annotations

from typing import Dict

from support_env.graders import GRADERS, grade_all
from support_env.models import FeedAction, Observation


def scripted_agent(obs: Observation) -> Dict:
    if obs.fatigue > 0.75:
        return FeedAction(action_type="suggest_break", break_minutes=7).model_dump()

    if obs.addiction_level > 0.7:
        return FeedAction(action_type="reorder_feed", strategy="prioritize_wellbeing").model_dump()

    safe_items = [x for x in obs.feed_items if x.category != "toxic"]
    target = safe_items[0] if safe_items else obs.feed_items[0]
    return FeedAction(action_type="recommend_item", item_id=target.id, rationale="scripted grader policy").model_dump()


def test_graders_return_bounded_scores() -> None:
    for task_id, grader in GRADERS.items():
        score = grader(scripted_agent, seed=42)
        assert task_id in {"easy", "medium", "hard"}
        assert 0.0 < score < 1.0


def test_grade_all_is_deterministic_for_fixed_seed() -> None:
    run_a = grade_all(scripted_agent, seed=77)
    run_b = grade_all(scripted_agent, seed=77)
    assert run_a == run_b


def test_grade_all_structure() -> None:
    scores = grade_all(scripted_agent, seed=42)
    assert set(scores.keys()) == {"easy", "medium", "hard", "overall"}
    assert 0.0 < scores["overall"] < 1.0
