from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Tuple

from .models import EnvInfo, FeedAction, FeedItem, Observation, Reward
from .tasks import TASKS


def _clip(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class AttentionEconomyEnv:
    """
    OpenEnv-style environment for simulating feed curation under attention constraints.

    Core interface:
    - reset(task_id, seed) -> Observation
    - step(action) -> (Observation, Reward, done, EnvInfo)
    - state() -> current state dictionary
    """

    def __init__(self, task_id: str = "easy", seed: int = 42) -> None:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Available: {list(TASKS.keys())}")
        self.task_id = task_id
        self.seed = seed
        self._rng = random.Random(seed)
        self._state: Dict[str, Any] = {}
        self.reset(task_id=task_id, seed=seed)

    def reset(self, task_id: str | None = None, seed: int | None = None) -> Observation:
        if task_id is not None:
            if task_id not in TASKS:
                raise ValueError(f"Unknown task_id '{task_id}'. Available: {list(TASKS.keys())}")
            self.task_id = task_id

        if seed is not None:
            self.seed = seed

        task = TASKS[self.task_id]
        self._rng = random.Random(self.seed + len(self.task_id))

        feed = copy.deepcopy(task["feed_pool"])
        self._rng.shuffle(feed)

        self._state = {
            "metrics": copy.deepcopy(task["initial_user"]),
            "feed": feed,
            "blocked_categories": set(),
            "recent_actions": [],
            "history": [],
            "time_remaining": int(task["time_budget"]),
            "step": 0,
            "max_steps": int(task["max_steps"]),
            "done": False,
            "total_reward": 0.0,
            "unsafe_events": 0,
            "loop_penalties": 0,
        }
        return self._make_observation("Environment reset. Start balancing engagement, productivity, and wellbeing.")

    def step(self, action: FeedAction) -> Tuple[Observation, Reward, bool, EnvInfo]:
        if self._state["done"]:
            raise RuntimeError("Episode already finished. Call reset() to start a new run.")

        if not isinstance(action, FeedAction):
            action = FeedAction(**action)

        before = copy.deepcopy(self._state["metrics"])
        penalty = 0.0
        info_error = ""

        try:
            action_reward_bonus = self._apply_action(action)
        except Exception as exc:  # pylint: disable=broad-except
            info_error = str(exc)
            penalty += 0.20
            action_reward_bonus = -0.10

        after = self._state["metrics"]
        delta_engagement = after["engagement"] - before["engagement"]
        delta_productivity = after["productivity"] - before["productivity"]
        delta_wellbeing = after["wellbeing"] - before["wellbeing"]

        if self._is_action_loop(action.action_type):
            penalty += 0.08
            self._state["loop_penalties"] += 1

        raw_reward = (
            0.35 * delta_engagement
            + 0.35 * delta_productivity
            + 0.30 * delta_wellbeing
            + action_reward_bonus
            - penalty
        )
        reward_value = _clip((raw_reward + 1.0) / 2.0)

        self._state["step"] += 1
        self._state["total_reward"] += reward_value

        if (
            self._state["step"] >= self._state["max_steps"]
            or self._state["time_remaining"] <= 0
            or self._state["metrics"]["fatigue"] >= 0.98
            or self._state["metrics"]["addiction_level"] >= 0.98
        ):
            self._state["done"] = True

        self._refresh_mood()
        obs = self._make_observation("Action applied." if not info_error else "Action failed with penalty.")

        reward = Reward(
            value=round(reward_value, 4),
            breakdown={
                "delta_engagement": round(delta_engagement, 4),
                "delta_productivity": round(delta_productivity, 4),
                "delta_wellbeing": round(delta_wellbeing, 4),
                "penalty": round(penalty, 4),
                "action_bonus": round(action_reward_bonus, 4),
            },
            message="Reward computed with dense trajectory shaping.",
        )

        average = self._state["total_reward"] / max(1, self._state["step"])
        info = EnvInfo(
            done=self._state["done"],
            total_reward=round(self._state["total_reward"], 4),
            average_reward=round(average, 4),
            unsafe_events=self._state["unsafe_events"],
            loop_penalties=self._state["loop_penalties"],
            processed_actions=len(self._state["history"]),
            error=info_error,
        )
        return obs, reward, self._state["done"], info

    def state(self) -> Dict[str, Any]:
        snapshot = copy.deepcopy(self._state)
        snapshot["blocked_categories"] = sorted(list(snapshot["blocked_categories"]))
        return snapshot

    def _apply_action(self, action: FeedAction) -> float:
        metrics = self._state["metrics"]

        if action.action_type == "recommend_item":
            if action.item_id is None:
                raise ValueError("item_id is required for action_type='recommend_item'.")

            item = self._find_feed_item(action.item_id)
            if item is None:
                raise ValueError(f"Item id {action.item_id} is not currently available in the feed.")

            if item["category"] in self._state["blocked_categories"]:
                raise ValueError(f"Category '{item['category']}' is blocked and cannot be recommended.")

            repeated_category_factor = self._recent_same_category_ratio(item["category"])
            engagement_gain = 0.55 * item["engagement_score"] + 0.20 * item["novelty_score"] - 0.25 * metrics["fatigue"]
            productivity_gain = 0.60 * item["productivity_score"] - 0.25 * item["toxicity_score"] - 0.15 * metrics["addiction_level"]
            addiction_increase = (
                0.50 * item["engagement_score"]
                + 0.50 * item["toxicity_score"]
                + 0.20 * repeated_category_factor
            )
            fatigue_increase = 0.35 * item["engagement_score"] + 0.35 * item["toxicity_score"] - 0.25 * metrics["energy"]
            energy_delta = -0.15 - 0.10 * item["toxicity_score"] + 0.05 * item["productivity_score"]

            metrics["engagement"] = _clip(metrics["engagement"] + 0.22 * engagement_gain)
            metrics["productivity"] = _clip(metrics["productivity"] + 0.20 * productivity_gain)
            metrics["addiction_level"] = _clip(metrics["addiction_level"] + 0.14 * addiction_increase)
            metrics["fatigue"] = _clip(metrics["fatigue"] + 0.16 * fatigue_increase)
            metrics["energy"] = _clip(metrics["energy"] + 0.20 * energy_delta)
            metrics["wellbeing"] = self._compute_wellbeing()

            self._state["time_remaining"] -= int(item["duration_min"])

            self._state["history"].append(
                {
                    "action": action.model_dump(),
                    "item": item,
                    "category": item["category"],
                }
            )
            self._state["feed"] = [x for x in self._state["feed"] if x["id"] != item["id"]]
            self._spawn_item()

            unsafe_penalty = 0.0
            if item["category"] == "toxic" and (
                metrics["addiction_level"] > 0.75 or metrics["fatigue"] > 0.75
            ):
                self._state["unsafe_events"] += 1
                unsafe_penalty = -0.20
            return unsafe_penalty

        if action.action_type == "block_category":
            if action.category is None:
                raise ValueError("category is required for action_type='block_category'.")
            self._state["blocked_categories"].add(action.category)
            self._state["feed"] = [x for x in self._state["feed"] if x["category"] != action.category]
            self._spawn_item()
            self._state["history"].append({"action": action.model_dump(), "category": action.category})
            if action.category == "toxic":
                metrics["wellbeing"] = _clip(metrics["wellbeing"] + 0.04)
                metrics["addiction_level"] = _clip(metrics["addiction_level"] - 0.03)
                return 0.04
            return -0.02

        if action.action_type == "suggest_break":
            minutes = action.break_minutes or 5
            metrics["energy"] = _clip(metrics["energy"] + min(0.25, 0.02 * minutes))
            metrics["fatigue"] = _clip(metrics["fatigue"] - min(0.30, 0.03 * minutes))
            metrics["addiction_level"] = _clip(metrics["addiction_level"] - min(0.20, 0.015 * minutes))
            metrics["engagement"] = _clip(metrics["engagement"] - 0.05)
            metrics["wellbeing"] = self._compute_wellbeing()
            self._state["time_remaining"] -= int(minutes)
            self._state["history"].append({"action": action.model_dump(), "minutes": minutes})
            return 0.02

        if action.action_type == "reorder_feed":
            strategy = action.strategy or "balanced"
            self._sort_feed(strategy)
            self._state["history"].append({"action": action.model_dump(), "strategy": strategy})
            bonus = 0.01
            if strategy == "prioritize_wellbeing" and self._state["metrics"]["addiction_level"] > 0.6:
                bonus = 0.03
            return bonus

        raise ValueError(f"Unsupported action_type '{action.action_type}'.")

    def _find_feed_item(self, item_id: int) -> Dict[str, Any] | None:
        visible = self._visible_feed_items()
        for item in visible:
            if item["id"] == item_id:
                return item
        return None

    def _visible_feed_items(self) -> List[Dict[str, Any]]:
        blocked = self._state["blocked_categories"]
        return [x for x in self._state["feed"] if x["category"] not in blocked]

    def _spawn_item(self) -> None:
        visible = self._visible_feed_items()
        if len(visible) >= 6:
            return

        task_pool = TASKS[self.task_id]["feed_pool"]
        used_ids = {item["id"] for item in self._state["feed"]}
        candidates = [x for x in task_pool if x["id"] not in used_ids and x["category"] not in self._state["blocked_categories"]]
        if not candidates:
            return

        self._state["feed"].append(copy.deepcopy(self._rng.choice(candidates)))

    def _sort_feed(self, strategy: str) -> None:
        if strategy == "prioritize_productivity":
            key_fn = lambda x: (x["productivity_score"], -x["toxicity_score"])  # noqa: E731
        elif strategy == "prioritize_engagement":
            key_fn = lambda x: (x["engagement_score"], x["novelty_score"])  # noqa: E731
        elif strategy == "prioritize_wellbeing":
            key_fn = lambda x: (x["productivity_score"] - x["toxicity_score"], -x["toxicity_score"])  # noqa: E731
        else:
            key_fn = lambda x: (0.5 * x["productivity_score"] + 0.5 * x["engagement_score"] - 0.4 * x["toxicity_score"])  # noqa: E731
        self._state["feed"].sort(key=key_fn, reverse=True)

    def _recent_same_category_ratio(self, category: str) -> float:
        recent = [h.get("category") for h in self._state["history"][-5:] if "category" in h]
        if not recent:
            return 0.0
        same = sum(1 for c in recent if c == category)
        return same / len(recent)

    def _is_action_loop(self, action_type: str) -> bool:
        self._state["recent_actions"].append(action_type)
        self._state["recent_actions"] = self._state["recent_actions"][-6:]
        last = self._state["recent_actions"][-4:]
        return len(last) == 4 and len(set(last)) == 1

    def _refresh_mood(self) -> None:
        m = self._state["metrics"]
        if m["fatigue"] > 0.75:
            mood = "tired"
        elif m["addiction_level"] > 0.72:
            mood = "overstimulated"
        elif m["productivity"] > 0.62 and m["energy"] > 0.50:
            mood = "focused"
        elif m["wellbeing"] > 0.60:
            mood = "calm"
        else:
            mood = "bored"
        m["mood"] = mood

    def _compute_wellbeing(self) -> float:
        m = self._state["metrics"]
        raw = 0.40 * m["productivity"] + 0.30 * m["energy"] + 0.20 * m["engagement"] - 0.30 * m["addiction_level"] - 0.20 * m["fatigue"]
        return _clip(raw + 0.25)

    def _make_observation(self, message: str) -> Observation:
        visible = self._visible_feed_items()[:6]
        feed_items = [FeedItem(**item) for item in visible]
        metrics = self._state["metrics"]

        return Observation(
            task_id=self.task_id,
            task_description=TASKS[self.task_id]["description"],
            seed=self.seed,
            session_step=self._state["step"],
            max_steps=self._state["max_steps"],
            time_remaining=self._state["time_remaining"],
            user_mood=metrics["mood"],
            energy=metrics["energy"],
            addiction_level=metrics["addiction_level"],
            fatigue=metrics["fatigue"],
            engagement=metrics["engagement"],
            productivity=metrics["productivity"],
            wellbeing=metrics["wellbeing"],
            blocked_categories=sorted(list(self._state["blocked_categories"])),
            feed_items=feed_items,
            recent_actions=list(self._state["recent_actions"]),
            done=self._state["done"],
            message=message,
        )
