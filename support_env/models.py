from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Mood = Literal["bored", "focused", "tired", "overstimulated", "calm"]
ContentType = Literal["reel", "article", "post", "thread", "video"]
Category = Literal["entertainment", "educational", "news", "social", "toxic"]
ActionType = Literal[
    "recommend_item",
    "block_category",
    "suggest_break",
    "reorder_feed",
]
ReorderStrategy = Literal[
    "prioritize_productivity",
    "prioritize_engagement",
    "prioritize_wellbeing",
    "balanced",
]


class FeedItem(BaseModel):
    id: int
    type: ContentType
    category: Category
    engagement_score: float = Field(ge=0.0, le=1.0)
    productivity_score: float = Field(ge=0.0, le=1.0)
    toxicity_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    duration_min: int = Field(ge=1, le=20)


class FeedAction(BaseModel):
    action_type: ActionType
    item_id: Optional[int] = None
    category: Optional[Category] = None
    break_minutes: Optional[int] = Field(default=None, ge=1, le=30)
    strategy: Optional[ReorderStrategy] = None
    rationale: str = ""


class Observation(BaseModel):
    task_id: str
    task_description: str
    seed: int
    session_step: int
    max_steps: int
    time_remaining: int
    user_mood: Mood
    energy: float = Field(ge=0.0, le=1.0)
    addiction_level: float = Field(ge=0.0, le=1.0)
    fatigue: float = Field(ge=0.0, le=1.0)
    engagement: float = Field(ge=0.0, le=1.0)
    productivity: float = Field(ge=0.0, le=1.0)
    wellbeing: float = Field(ge=0.0, le=1.0)
    blocked_categories: List[Category] = Field(default_factory=list)
    feed_items: List[FeedItem] = Field(default_factory=list)
    recent_actions: List[str] = Field(default_factory=list)
    done: bool = False
    message: str = ""


class Reward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str = ""


class EnvInfo(BaseModel):
    done: bool
    total_reward: float
    average_reward: float
    unsafe_events: int
    loop_penalties: int
    processed_actions: int
    error: str = ""
