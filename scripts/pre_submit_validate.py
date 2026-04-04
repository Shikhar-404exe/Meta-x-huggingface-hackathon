from __future__ import annotations

import json
import sys
from typing import Dict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from app import app
from support_env.graders import grade_all
from support_env.models import FeedAction, Observation


client = TestClient(app)


def scripted_agent(obs: Observation) -> Dict:
    if obs.fatigue > 0.75:
        return FeedAction(action_type="suggest_break", break_minutes=7).model_dump()
    if obs.addiction_level > 0.7:
        return FeedAction(action_type="reorder_feed", strategy="prioritize_wellbeing").model_dump()

    safe = [x for x in obs.feed_items if x.category != "toxic"]
    chosen = safe[0] if safe else obs.feed_items[0]
    return FeedAction(action_type="recommend_item", item_id=chosen.id, rationale="validator policy").model_dump()


def check_api() -> Dict[str, bool]:
    checks = {}

    health = client.get("/health")
    checks["health_200"] = health.status_code == 200

    tasks = client.get("/tasks")
    checks["tasks_200"] = tasks.status_code == 200
    task_payload = tasks.json().get("tasks", []) if tasks.status_code == 200 else []
    checks["three_plus_tasks"] = len(task_payload) >= 3

    for task in ["easy", "medium", "hard"]:
        reset = client.post("/reset", json={"task_id": task, "seed": 42})
        checks[f"reset_{task}"] = reset.status_code == 200
        if reset.status_code != 200:
            continue

        obs = reset.json()
        loops = 0
        done = False

        while not done and loops < 80:
            loops += 1
            feed = obs.get("feed_items", [])
            if not feed:
                action = {
                    "action_type": "suggest_break",
                    "break_minutes": 5,
                    "rationale": "No feed items",
                }
            else:
                safe = [x for x in feed if x.get("category") != "toxic"]
                chosen = safe[0] if safe else feed[0]
                action = {
                    "action_type": "recommend_item",
                    "item_id": chosen["id"],
                    "rationale": "Validator rollout",
                }

            step = client.post("/step", json={"task_id": task, "action": action})
            checks[f"step_{task}_200"] = checks.get(f"step_{task}_200", True) and step.status_code == 200
            if step.status_code != 200:
                break

            payload = step.json()
            reward = payload["reward"]["value"]
            in_range = 0.0 <= reward <= 1.0
            checks[f"reward_range_{task}"] = checks.get(f"reward_range_{task}", True) and in_range

            done = bool(payload["done"])
            obs = payload["observation"]

        checks[f"episode_ends_{task}"] = done

    return checks


def check_graders() -> Dict[str, bool]:
    checks = {}
    run_a = grade_all(scripted_agent, seed=42)
    run_b = grade_all(scripted_agent, seed=42)

    checks["graders_deterministic"] = run_a == run_b
    checks["grader_keys"] = set(run_a.keys()) == {"easy", "medium", "hard", "overall"}
    checks["grader_score_bounds"] = all(0.0 <= v <= 1.0 for v in run_a.values())

    print("Baseline deterministic grader scores:")
    print(json.dumps(run_a, indent=2))
    return checks


def main() -> None:
    results = {}
    results.update(check_api())
    results.update(check_graders())

    print("\nValidation checklist:")
    for name, ok in results.items():
        marker = "PASS" if ok else "FAIL"
        print(f"- {name}: {marker}")

    failed = [k for k, v in results.items() if not v]
    if failed:
        print("\nPre-submit validation failed.")
        sys.exit(1)

    print("\nPre-submit validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
