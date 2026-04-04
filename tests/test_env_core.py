from __future__ import annotations

from support_env.env import AttentionEconomyEnv
from support_env.models import FeedAction


def policy_action(obs):
    if obs.fatigue > 0.78:
        return FeedAction(action_type="suggest_break", break_minutes=7)
    safe_items = [x for x in obs.feed_items if x.category != "toxic"]
    if obs.addiction_level > 0.72:
        return FeedAction(action_type="reorder_feed", strategy="prioritize_wellbeing")
    if safe_items:
        return FeedAction(action_type="recommend_item", item_id=safe_items[0].id)
    if obs.feed_items:
        return FeedAction(action_type="recommend_item", item_id=obs.feed_items[0].id)
    return FeedAction(action_type="suggest_break", break_minutes=5)


def test_reset_returns_valid_observation() -> None:
    env = AttentionEconomyEnv(task_id="easy", seed=42)
    obs = env.reset(task_id="easy", seed=42)

    assert obs.task_id == "easy"
    assert obs.seed == 42
    assert obs.session_step == 0
    assert obs.max_steps > 0
    assert 0.0 <= obs.engagement <= 1.0
    assert len(obs.feed_items) > 0


def test_step_reward_range_and_progress() -> None:
    env = AttentionEconomyEnv(task_id="easy", seed=42)
    obs = env.reset(task_id="easy", seed=42)
    action = policy_action(obs)

    next_obs, reward, done, info = env.step(action)

    assert 0.0 <= reward.value <= 1.0
    assert next_obs.session_step == 1
    assert info.processed_actions == 1
    assert done in {True, False}


def test_invalid_action_penalized() -> None:
    env = AttentionEconomyEnv(task_id="easy", seed=42)
    env.reset(task_id="easy", seed=42)

    # Invalid item_id should not crash step(); it should record an error and apply penalty.
    obs, reward, _, info = env.step(FeedAction(action_type="recommend_item", item_id=999999))

    assert reward.breakdown["penalty"] >= 0.2
    assert info.error != ""
    assert obs.session_step == 1


def test_deterministic_trajectory() -> None:
    env_a = AttentionEconomyEnv(task_id="medium", seed=99)
    env_b = AttentionEconomyEnv(task_id="medium", seed=99)

    obs_a = env_a.reset(task_id="medium", seed=99)
    obs_b = env_b.reset(task_id="medium", seed=99)

    for _ in range(8):
        act_a = policy_action(obs_a)
        act_b = policy_action(obs_b)

        obs_a, rew_a, done_a, _ = env_a.step(act_a)
        obs_b, rew_b, done_b, _ = env_b.step(act_b)

        assert rew_a.value == rew_b.value
        assert obs_a.engagement == obs_b.engagement
        assert obs_a.productivity == obs_b.productivity
        assert obs_a.wellbeing == obs_b.wellbeing
        assert done_a == done_b

        if done_a:
            break


def test_episode_eventually_ends() -> None:
    env = AttentionEconomyEnv(task_id="hard", seed=7)
    obs = env.reset(task_id="hard", seed=7)
    done = False

    for _ in range(60):
        action = policy_action(obs)
        obs, _, done, _ = env.step(action)
        if done:
            break

    assert done is True
    assert obs.done is True
