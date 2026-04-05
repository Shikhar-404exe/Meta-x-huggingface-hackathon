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

## Attention Economy Simulator

We built this OpenEnv benchmark to test responsible feed curation in a practical, real-world style setting.

In this environment, our agent tries to balance three goals at the same time:

- Engagement
- Productivity
- Long-term wellbeing

In simple terms, we do not want to maximize clicks at the cost of user health.

## Project links

- GitHub: https://github.com/Shikhar-404exe/Meta-x-huggingface-hackathon
- Hugging Face Space: https://huggingface.co/spaces/Shikhar9000/meta_hack

## What the API provides

- POST /reset
- POST /step
- GET /state
- GET /tasks
- GET /health

For compatibility:

- /reset accepts query params or JSON body
- /step accepts wrapped payload or direct action JSON

## Tasks

- easy: Healthy Engagement Basics
- medium: Balanced Feed Curation
- hard: Long-Horizon Wellbeing Recovery

We keep grading deterministic, and every score is clamped to 0.0-1.0.

## Quick start (Windows)

```powershell
cd "C:\Users\shash\Desktop\Meta X HuggingFace Hackathon"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then, in a second terminal, we can run baseline inference:

```powershell
cd "C:\Users\shash\Desktop\Meta X HuggingFace Hackathon"
.\.venv\Scripts\Activate.ps1
$env:ENV_URL="https://shikhar9000-meta-hack.hf.space"
$env:API_BASE_URL="https://router.huggingface.co/v1"
$env:MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
$env:HF_TOKEN="<your_hf_token>"
python inference.py
```

## Environment variables used by inference.py

Required:

- API_BASE_URL
- MODEL_NAME
- HF_TOKEN

Optional:

- OPENAI_API_KEY (fallback if HF_TOKEN is not set)
- ENV_URL (default: http://localhost:7860)

## Validation commands

```powershell
pytest -q
python scripts/pre_submit_validate.py
& ".\.venv\Scripts\openenv.exe" validate
```

## Baseline result (seed=42)

| Task    |  Score |
| ------- | -----: |
| easy    | 0.5131 |
| medium  | 0.1654 |
| hard    | 0.0000 |
| overall | 0.2262 |

The script writes these values to baseline_scores.json and logs structured events in START/STEP/END format.

## Screenshots

We captured the following proof screenshots for submission:

- OpenEnv validate success output
- pre_submit_validate.py passing output
- Hugging Face Space running container status
- Hugging Face Space build logs
- Inference run finishing with END log

Note: We are not storing PNG screenshots inside this repository because the Hugging Face Space Git remote rejects binary files unless Xet storage is configured.

## Submission checklist

- [x] Environment implemented with typed models and OpenEnv endpoints
- [x] Three tasks with deterministic graders
- [x] Baseline inference script with required env vars and START/STEP/END logs
- [x] Dockerized and deployed on Hugging Face Space
- [x] openenv validate passes
- [x] Pre-submit validator passes
