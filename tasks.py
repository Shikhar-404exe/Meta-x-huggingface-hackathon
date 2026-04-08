from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from support_env.tasks import TASKS as SUPPORT_TASKS

# Root-level task export for validators that discover tasks via `import tasks`.
TASKS = SUPPORT_TASKS


def get_tasks() -> Mapping[str, dict[str, Any]]:
    return TASKS
