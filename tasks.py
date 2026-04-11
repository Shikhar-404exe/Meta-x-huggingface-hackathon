from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from support_env.tasks import TASKS as SUPPORT_TASKS
from support_env.tasks import TASKS_LIST as SUPPORT_TASKS_LIST
from support_env.tasks import TASK_IDS as SUPPORT_TASK_IDS

# Root-level task export for validators that discover tasks via `import tasks`.
TASKS = SUPPORT_TASKS
TASKS_LIST = SUPPORT_TASKS_LIST
TASK_IDS = SUPPORT_TASK_IDS
TASK_REGISTRY = TASKS
TASK_DEFINITIONS = TASKS


def get_tasks() -> Mapping[str, dict[str, Any]]:
    return TASKS


def list_tasks() -> list[dict[str, Any]]:
    return TASKS_LIST


def task_ids() -> tuple[str, ...]:
    return TASK_IDS
