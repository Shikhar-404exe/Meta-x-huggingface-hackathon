from __future__ import annotations

from typing import Any, Dict

TASKS_MODULE = "support_env.tasks"
GRADERS_MODULE = "graders"

# Deterministic task definitions with fixed parameters and feed pools.
TASKS: Dict[str, Dict[str, Any]] = {
    "easy": {
        "id": "easy",
        "name": "Healthy Engagement Basics",
        "difficulty": "easy",
        "description": "Maintain engagement while preventing addiction spikes for a casual user session.",
        "max_steps": 14,
        "grader": "graders.grade_easy",
        "python_module": TASKS_MODULE,
        "task_key": "easy",
        "grader_module": GRADERS_MODULE,
        "time_budget": 45,
        "initial_user": {
            "mood": "bored",
            "energy": 0.70,
            "addiction_level": 0.25,
            "fatigue": 0.20,
            "engagement": 0.45,
            "productivity": 0.35,
            "wellbeing": 0.58,
        },
        "feed_pool": [
            {"id": 1001, "type": "reel", "category": "entertainment", "engagement_score": 0.88, "productivity_score": 0.08, "toxicity_score": 0.20, "novelty_score": 0.70, "duration_min": 2},
            {"id": 1002, "type": "article", "category": "educational", "engagement_score": 0.55, "productivity_score": 0.90, "toxicity_score": 0.02, "novelty_score": 0.60, "duration_min": 6},
            {"id": 1003, "type": "post", "category": "social", "engagement_score": 0.68, "productivity_score": 0.20, "toxicity_score": 0.10, "novelty_score": 0.45, "duration_min": 3},
            {"id": 1004, "type": "thread", "category": "news", "engagement_score": 0.64, "productivity_score": 0.62, "toxicity_score": 0.15, "novelty_score": 0.50, "duration_min": 5},
            {"id": 1005, "type": "video", "category": "toxic", "engagement_score": 0.86, "productivity_score": 0.04, "toxicity_score": 0.82, "novelty_score": 0.72, "duration_min": 4},
            {"id": 1006, "type": "article", "category": "educational", "engagement_score": 0.58, "productivity_score": 0.88, "toxicity_score": 0.01, "novelty_score": 0.62, "duration_min": 7},
            {"id": 1007, "type": "reel", "category": "entertainment", "engagement_score": 0.80, "productivity_score": 0.07, "toxicity_score": 0.24, "novelty_score": 0.66, "duration_min": 2},
            {"id": 1008, "type": "post", "category": "social", "engagement_score": 0.60, "productivity_score": 0.28, "toxicity_score": 0.12, "novelty_score": 0.42, "duration_min": 3},
        ],
    },
    "medium": {
        "id": "medium",
        "name": "Balanced Feed Curation",
        "difficulty": "medium",
        "description": "Balance engagement and productivity while preserving content diversity in a mixed feed.",
        "max_steps": 18,
        "grader": "graders.grade_medium",
        "python_module": TASKS_MODULE,
        "task_key": "medium",
        "grader_module": GRADERS_MODULE,
        "time_budget": 55,
        "initial_user": {
            "mood": "focused",
            "energy": 0.65,
            "addiction_level": 0.35,
            "fatigue": 0.30,
            "engagement": 0.50,
            "productivity": 0.45,
            "wellbeing": 0.55,
        },
        "feed_pool": [
            {"id": 2001, "type": "article", "category": "educational", "engagement_score": 0.60, "productivity_score": 0.92, "toxicity_score": 0.02, "novelty_score": 0.58, "duration_min": 8},
            {"id": 2002, "type": "thread", "category": "news", "engagement_score": 0.71, "productivity_score": 0.65, "toxicity_score": 0.20, "novelty_score": 0.54, "duration_min": 6},
            {"id": 2003, "type": "reel", "category": "entertainment", "engagement_score": 0.90, "productivity_score": 0.05, "toxicity_score": 0.28, "novelty_score": 0.77, "duration_min": 2},
            {"id": 2004, "type": "video", "category": "toxic", "engagement_score": 0.87, "productivity_score": 0.03, "toxicity_score": 0.91, "novelty_score": 0.75, "duration_min": 4},
            {"id": 2005, "type": "post", "category": "social", "engagement_score": 0.67, "productivity_score": 0.23, "toxicity_score": 0.16, "novelty_score": 0.49, "duration_min": 3},
            {"id": 2006, "type": "article", "category": "educational", "engagement_score": 0.56, "productivity_score": 0.86, "toxicity_score": 0.03, "novelty_score": 0.61, "duration_min": 7},
            {"id": 2007, "type": "thread", "category": "news", "engagement_score": 0.63, "productivity_score": 0.70, "toxicity_score": 0.14, "novelty_score": 0.52, "duration_min": 5},
            {"id": 2008, "type": "reel", "category": "entertainment", "engagement_score": 0.84, "productivity_score": 0.09, "toxicity_score": 0.22, "novelty_score": 0.69, "duration_min": 2},
            {"id": 2009, "type": "post", "category": "social", "engagement_score": 0.62, "productivity_score": 0.26, "toxicity_score": 0.18, "novelty_score": 0.46, "duration_min": 3},
        ],
    },
    "hard": {
        "id": "hard",
        "name": "Long-Horizon Wellbeing Recovery",
        "difficulty": "hard",
        "description": "Recover wellbeing from a high-risk, high-toxicity session while keeping engagement and productivity functional.",
        "max_steps": 24,
        "grader": "graders.grade_hard",
        "python_module": TASKS_MODULE,
        "task_key": "hard",
        "grader_module": GRADERS_MODULE,
        "time_budget": 65,
        "initial_user": {
            "mood": "overstimulated",
            "energy": 0.42,
            "addiction_level": 0.72,
            "fatigue": 0.66,
            "engagement": 0.58,
            "productivity": 0.30,
            "wellbeing": 0.34,
        },
        "feed_pool": [
            {"id": 3001, "type": "video", "category": "toxic", "engagement_score": 0.93, "productivity_score": 0.01, "toxicity_score": 0.95, "novelty_score": 0.79, "duration_min": 4},
            {"id": 3002, "type": "reel", "category": "entertainment", "engagement_score": 0.89, "productivity_score": 0.04, "toxicity_score": 0.33, "novelty_score": 0.72, "duration_min": 2},
            {"id": 3003, "type": "article", "category": "educational", "engagement_score": 0.53, "productivity_score": 0.95, "toxicity_score": 0.01, "novelty_score": 0.60, "duration_min": 9},
            {"id": 3004, "type": "thread", "category": "news", "engagement_score": 0.66, "productivity_score": 0.74, "toxicity_score": 0.18, "novelty_score": 0.56, "duration_min": 6},
            {"id": 3005, "type": "post", "category": "social", "engagement_score": 0.72, "productivity_score": 0.18, "toxicity_score": 0.23, "novelty_score": 0.48, "duration_min": 3},
            {"id": 3006, "type": "video", "category": "toxic", "engagement_score": 0.91, "productivity_score": 0.02, "toxicity_score": 0.92, "novelty_score": 0.74, "duration_min": 4},
            {"id": 3007, "type": "article", "category": "educational", "engagement_score": 0.57, "productivity_score": 0.90, "toxicity_score": 0.02, "novelty_score": 0.63, "duration_min": 8},
            {"id": 3008, "type": "thread", "category": "news", "engagement_score": 0.62, "productivity_score": 0.69, "toxicity_score": 0.20, "novelty_score": 0.53, "duration_min": 6},
            {"id": 3009, "type": "reel", "category": "entertainment", "engagement_score": 0.85, "productivity_score": 0.07, "toxicity_score": 0.30, "novelty_score": 0.67, "duration_min": 2},
            {"id": 3010, "type": "post", "category": "social", "engagement_score": 0.65, "productivity_score": 0.21, "toxicity_score": 0.19, "novelty_score": 0.45, "duration_min": 3},
        ],
    },
}

# Alternate registry exports used by some validator harnesses.
TASKS_LIST = list(TASKS.values())
TASK_IDS = tuple(TASKS.keys())
