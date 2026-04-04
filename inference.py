from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860").rstrip("/")

if not API_BASE_URL:
    raise SystemExit("Missing required env var: API_BASE_URL")
if not MODEL_NAME:
    raise SystemExit("Missing required env var: MODEL_NAME")
API_KEY = HF_TOKEN or OPENAI_API_KEY
if not API_KEY:
    raise SystemExit("Missing API key: set HF_TOKEN or OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
MODEL = MODEL_NAME


def _emit(tag: str, payload: Dict[str, Any]) -> None:
    # Structured stdout logs for evaluator parsing.
    print(f"[{tag}] {json.dumps(payload, separators=(',', ':'), ensure_ascii=True)}")


def log_start(task: str, env: str, model: str) -> None:
    _emit("START", {"task": task, "env": env, "model": model})


def log_step(step: int, action: str, reward: float, done: bool, error: str | None) -> None:
    _emit(
        "STEP",
        {
            "step": step,
            "action": action,
            "reward": round(float(reward), 4),
            "done": bool(done),
            "error": error,
        },
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    _emit(
        "END",
        {
            "success": bool(success),
            "steps": int(steps),
            "score": round(float(score), 4),
            "rewards": [round(float(r), 4) for r in rewards],
        },
    )

SYSTEM_PROMPT = """You are an attention-economy feed curator agent.
You must return ONLY valid JSON with this schema:
{
  "action_type": "recommend_item | block_category | suggest_break | reorder_feed",
  "item_id": int|null,
  "category": "entertainment|educational|news|social|toxic"|null,
  "break_minutes": int|null,
  "strategy": "prioritize_productivity|prioritize_engagement|prioritize_wellbeing|balanced"|null,
  "rationale": "short reason"
}

Policy rules:
- If addiction_level or fatigue is high, avoid toxic recommendations.
- Keep engagement without sacrificing productivity and wellbeing.
- Use suggest_break when fatigue is high.
- Use block_category for toxic when session risk is rising.
"""


def _strip_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object in model output")
    return json.loads(cleaned[start : end + 1])


def _heuristic_action(obs: Dict[str, Any]) -> Dict[str, Any]:
    fatigue = float(obs.get("fatigue", 0.0))
    addiction = float(obs.get("addiction_level", 0.0))
    feed_items = obs.get("feed_items", [])

    if fatigue > 0.75:
        return {
            "action_type": "suggest_break",
            "break_minutes": 8,
            "item_id": None,
            "category": None,
            "strategy": None,
            "rationale": "High fatigue recovery break",
        }

    if addiction > 0.70:
        return {
            "action_type": "reorder_feed",
            "strategy": "prioritize_wellbeing",
            "item_id": None,
            "category": None,
            "break_minutes": None,
            "rationale": "Reduce compulsive drift",
        }

    safe_items = [x for x in feed_items if x.get("category") != "toxic"]
    candidates = safe_items if safe_items else feed_items

    if not candidates:
        return {
            "action_type": "suggest_break",
            "break_minutes": 5,
            "item_id": None,
            "category": None,
            "strategy": None,
            "rationale": "No candidates in feed",
        }

    best = max(candidates, key=lambda x: (0.55 * x.get("productivity_score", 0.0) + 0.45 * x.get("engagement_score", 0.0) - 0.6 * x.get("toxicity_score", 0.0)))
    return {
        "action_type": "recommend_item",
        "item_id": best.get("id"),
        "category": None,
        "break_minutes": None,
        "strategy": None,
        "rationale": "Balanced productivity and engagement",
    }


def _llm_action(obs: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            temperature=0.0,
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(obs, indent=2)},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        data = _strip_json(raw)
        data.setdefault("item_id", None)
        data.setdefault("category", None)
        data.setdefault("break_minutes", None)
        data.setdefault("strategy", None)
        data.setdefault("rationale", "")
        return data
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return _heuristic_action(obs)


def _run_task(task_id: str, seed: int = 42, step_offset: int = 0) -> tuple[float, int, list[float]]:
    reset_resp = requests.post(
        f"{ENV_URL}/reset",
        json={"task_id": task_id, "seed": seed},
        timeout=30,
    )
    reset_resp.raise_for_status()
    obs = reset_resp.json()

    done = False
    safety_guard = 0
    rewards: list[float] = []
    while not done and safety_guard < 100:
        safety_guard += 1
        action = _llm_action(obs)

        step_resp = requests.post(
            f"{ENV_URL}/step",
            json={"task_id": task_id, "action": action},
            timeout=30,
        )
        step_resp.raise_for_status()
        payload = step_resp.json()
        obs = payload["observation"]
        done = bool(payload["done"])

        reward_value = payload.get("reward", {}).get("value", 0.0)
        rewards.append(float(reward_value))
        action_str = json.dumps(action, separators=(",", ":"), ensure_ascii=True)
        log_step(step=step_offset + safety_guard, action=action_str, reward=float(reward_value), done=done, error=None)

    state_resp = requests.get(f"{ENV_URL}/state", params={"task_id": task_id}, timeout=30)
    state_resp.raise_for_status()
    state = state_resp.json()

    metrics = state["metrics"]
    unsafe = state["unsafe_events"]
    loops = state["loop_penalties"]

    if task_id == "easy":
        score = 0.60 * metrics["engagement"] + 0.40 * (1.0 - metrics["addiction_level"]) - (0.08 * unsafe + 0.04 * loops)
    elif task_id == "medium":
        # Use unique category ratio from history as diversity component.
        history_categories = [h.get("category") for h in state["history"] if h.get("category")]
        diversity = (len(set(history_categories)) / len(history_categories)) if history_categories else 0.0
        score = 0.45 * metrics["engagement"] + 0.45 * metrics["productivity"] + 0.10 * diversity - (0.08 * unsafe + 0.05 * loops)
    else:
        score = 0.30 * metrics["engagement"] + 0.25 * metrics["productivity"] + 0.45 * metrics["wellbeing"] - (0.12 * unsafe + 0.05 * loops)

    return round(max(0.0, min(1.0, score)), 4), safety_guard, rewards


def main() -> None:
    health = requests.get(f"{ENV_URL}/health", timeout=15)
    health.raise_for_status()

    task_name = "all_tasks"
    benchmark = "attention-economy-simulator"
    log_start(task=task_name, env=benchmark, model=MODEL)

    scores = {}
    all_step_rewards: list[float] = []
    total_steps = 0
    for task_id in ["easy", "medium", "hard"]:
        score, steps_taken, rewards = _run_task(task_id=task_id, seed=42, step_offset=total_steps)
        scores[task_id] = score
        total_steps += steps_taken
        all_step_rewards.extend(rewards)

    overall = round(sum(scores.values()) / 3.0, 4)
    scores["overall"] = overall

    with open("baseline_scores.json", "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    # Success threshold for summary logging only.
    success = overall >= 0.2
    log_end(success=success, steps=total_steps, score=overall, rewards=all_step_rewards)


if __name__ == "__main__":
    main()
