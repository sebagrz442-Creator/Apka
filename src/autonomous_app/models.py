from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Step:
    name: str
    prompt: str


@dataclass(frozen=True)
class Plan:
    name: str
    interval_seconds: int
    max_iterations: int
    allowed_tools: tuple[str, ...]
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class ToolAction:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    content: str
    is_error: bool = False
