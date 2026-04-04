---
title: Attention Economy Simulator
emoji: "📘"
colorFrom: blue
colorTo: green
sdk: docker
tags:
  - openenv
  - digital-wellbeing
  - recommendation-systems
---

## Attention Economy Simulator (OpenEnv)

A real-world OpenEnv environment where an AI agent manages digital feed decisions to balance:

- Engagement
- Productivity
- Long-term wellbeing

## Why this environment matters

Modern recommendation systems optimize watch time aggressively, often at the expense of user health and focus. This environment models that practical tradeoff so agentic systems can be benchmarked on responsible curation behavior.

## Environment API

- `POST /reset` -> returns initial `Observation`
- `POST /step` -> returns `{observation, reward, done, info}`
- `GET /state` -> returns current internal state
- `GET /tasks` -> returns task catalog
- `GET /health` -> service health check

Request compatibility hardening:

- `/reset` accepts either query params (`task_id`, `seed`) or JSON body
- `/step` accepts either wrapped payload (`{"task_id": ..., "action": {...}}`) or direct action JSON

## Typed spaces

### Observation

Observation includes user state (`mood`, `energy`, `addiction_level`, `fatigue`, `engagement`, `productivity`, `wellbeing`), current feed items, blocked categories, and episode counters.

### Action

Action schema:

```json
{
  "action_type": "recommend_item | block_category | suggest_break | reorder_feed",
  "item_id": 1002,
  "category": "toxic",
  "break_minutes": 8,
  "strategy": "prioritize_wellbeing",
  "rationale": "optional short reason"
}
```

## Reward function

Dense trajectory reward each step:

- `0.35 * delta_engagement`
- `0.35 * delta_productivity`
- `0.30 * delta_wellbeing`

With penalties for invalid/unsafe/repetitive behavior. Final per-step reward is clipped to `[0.0, 1.0]`.

## Tasks and deterministic graders

1. Easy: Healthy Engagement Basics
   Score objective: engagement high while addiction low.

2. Medium: Balanced Feed Curation
   Score objective: engagement + productivity + diversity.

3. Hard: Long-Horizon Wellbeing Recovery
   Score objective: maximize wellbeing under high-risk initial state.

All graders are deterministic with fixed seeds and clamp scores to `0.0-1.0`.

## Local setup

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Copy `.env.example` to `.env` and fill your API values before running `inference.py`.

## Docker

```bash
docker build -t attention-economy-simulator .
docker run -p 7860:7860 attention-economy-simulator
```

## Baseline inference

`inference.py` is in project root and uses OpenAI client.

Required environment variables:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Optional:

- `OPENAI_API_KEY` (fallback)
- `ENV_URL` (defaults to `http://localhost:7860`)

Run baseline:

```bash
python inference.py
```

Outputs per-task scores and writes `baseline_scores.json`.
The script also emits structured stdout events in `[START]`, `[STEP]`, and `[END]` format for evaluator parsing.

### Baseline scores (`inference.py`, seed=42)

| Task    |  Score |
| ------- | -----: |
| easy    | 0.5131 |
| medium  | 0.1654 |
| hard    | 0.0000 |
| overall | 0.2262 |

These values come from an actual `inference.py` run against the deployed environment with fixed seed.

## Tests and validation

Run unit tests:

```bash
pytest -q
```

Run local pre-submit validator:

```bash
python scripts/pre_submit_validate.py
```

The validator checks:

- API health and endpoint behavior (`/health`, `/reset`, `/step`, `/state`, `/tasks`)
- 3+ tasks available
- Reward range compliance (`0.0-1.0`)
- Episode termination behavior
- Deterministic grader outputs

## Hugging Face Space deployment

1. Create a new Docker Space.
2. Push this repository.
3. Configure Space variables:
   - `API_BASE_URL`
   - `MODEL_NAME`
4. Configure Space secrets:
   - `HF_TOKEN`
   - `OPENAI_API_KEY` (optional fallback)
5. Ensure the app responds on port `7860`.

Current Space: `https://huggingface.co/spaces/Shikhar9000/meta_hack`

## Pre-submission checklist

- [ ] Space deploys and `/health` returns 200
- [ ] `/reset`, `/step`, `/state`, `/tasks` behave correctly
- [ ] `openenv.yaml` present and valid
- [ ] 3 deterministic tasks + graders with scores in `[0.0, 1.0]`
- [ ] Docker build and run succeed
- [ ] `inference.py` runs and outputs reproducible baseline
- [ ] Runtime suitable for 2 vCPU / 8 GB
