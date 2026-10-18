from typing import Any, Protocol

from .copilot import CopilotError
from .models import Plan, Step, ToolAction
from .tools import LocalMCPTools, ToolError


class ModelClient(Protocol):
    def next_action(self, step: Step, history: list[dict[str, Any]]) -> ToolAction | None: ...


class Agent:
    def __init__(self, model: ModelClient, tools: LocalMCPTools) -> None:
        self.model = model
        self.tools = tools

    def run_plan(self, plan: Plan) -> None:
        for step in plan.steps:
            history: list[dict[str, Any]] = []
            for _ in range(plan.max_iterations):
                action = self.model.next_action(step, history)
                if action is None:
                    break
                try:
                    result = self.tools.call_tool(
                        action.tool, action.arguments, plan.allowed_tools
                    )
                    history.append(
                        {
                            "tool": action.tool,
                            "arguments": action.arguments,
                            "result": result.content,
                            "is_error": result.is_error,
                        }
                    )
                except ToolError as exc:
                    history.append({"tool": action.tool, "error": str(exc)})
            else:
                raise CopilotError(
                    f"Step '{step.name}' exceeded its {plan.max_iterations}-iteration limit."
                )
