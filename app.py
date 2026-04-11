from __future__ import annotations

from typing import Dict

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from support_env.env import AttentionEconomyEnv
from support_env.models import EnvInfo, FeedAction, Observation, Reward
from support_env.tasks import TASKS

app = FastAPI(
    title="Attention Economy Simulator",
    description="OpenEnv-compatible environment for balancing engagement, productivity, and wellbeing.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_env_sessions: Dict[str, AttentionEconomyEnv] = {}


class ResetRequest(BaseModel):
    task_id: str = "easy"
    seed: int = 42


class StepRequest(BaseModel):
    task_id: str = "easy"
    action: FeedAction


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: EnvInfo


def _parse_reset_request(body: dict, task_id_q: str | None, seed_q: int | None) -> ResetRequest:
    task_id = task_id_q or body.get("task_id", "easy")
    seed = seed_q if seed_q is not None else body.get("seed", 42)
    try:
        return ResetRequest(task_id=task_id, seed=int(seed))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=422, detail=f"Invalid reset payload: {exc}") from exc


def _parse_step_request(body: dict, task_id_q: str | None) -> tuple[str, FeedAction]:
    if "action" in body and isinstance(body["action"], dict):
        task_id = task_id_q or body.get("task_id", "easy")
        action_payload = dict(body["action"])
    else:
        task_id = task_id_q or body.get("task_id", "easy")
        action_payload = dict(body)
        action_payload.pop("task_id", None)

    if "action_type" not in action_payload:
        raise HTTPException(
            status_code=422,
            detail="Step payload must include action_type or be wrapped as {'task_id': ..., 'action': {...}}.",
        )

    try:
        action = FeedAction.model_validate(action_payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid action payload: {exc}") from exc

    return task_id, action


def _get_env(task_id: str) -> AttentionEconomyEnv:
    env = _env_sessions.get(task_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"No active session for task '{task_id}'. Call /reset first.")
    return env


@app.get("/")
def root() -> dict:
    return {
        "name": "Attention Economy Simulator",
        "status": "running",
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health", "/docs"],
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "environment": "attention-economy-simulator",
        "version": "1.0.0",
    }


@app.post("/reset", response_model=Observation)
async def reset(
    request: Request,
    task_id: str | None = Query(default=None),
    seed: int | None = Query(default=None),
) -> Observation:
    try:
        body = await request.json()
    except Exception:
        body = {}

    req = _parse_reset_request(body if isinstance(body, dict) else {}, task_id, seed)

    if req.task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id '{req.task_id}'.")

    env = AttentionEconomyEnv(task_id=req.task_id, seed=req.seed)
    _env_sessions[req.task_id] = env
    return env.reset(task_id=req.task_id, seed=req.seed)


@app.post("/step", response_model=StepResponse)
async def step(
    request: Request,
    task_id: str | None = Query(default=None),
) -> StepResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_id_value, action = _parse_step_request(body if isinstance(body, dict) else {}, task_id)
    env = _get_env(task_id_value)

    try:
        observation, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StepResponse(
        observation=observation,
        reward=reward,
        done=done,
        info=info,
    )


@app.get("/state")
def state(task_id: str = "easy") -> dict:
    env = _get_env(task_id)
    return env.state()


@app.get("/tasks")
def tasks() -> dict:
    payload = []
    for task in TASKS.values():
        payload.append(
            {
                "id": task["id"],
                "name": task["name"],
                "difficulty": task["difficulty"],
                "description": task["description"],
                "max_steps": task["max_steps"],
                "time_budget": task["time_budget"],
                "grader": task.get("grader"),
                "python_module": task.get("python_module"),
                "task_key": task.get("task_key"),
                "grader_module": task.get("grader_module"),
            }
        )
    return {"tasks": payload}
