import tempfile
import unittest
from pathlib import Path

from autonomous_app.agent import Agent
from autonomous_app.models import Plan, Step, ToolAction
from autonomous_app.tools import LocalMCPTools, ToolError


class FakeModel:
    def __init__(self, actions: list[ToolAction | None]) -> None:
        self.actions = iter(actions)

    def next_action(self, step: Step, history: list[dict]) -> ToolAction | None:
        return next(self.actions)


class AgentTests(unittest.TestCase):
    def test_runs_allowlisted_action_then_finishes(self) -> None:
        model = FakeModel([ToolAction("echo", {"text": "hello"}), None])
        plan = Plan("test", 0, 2, ("echo",), (Step("test", "echo"),))
        with tempfile.TemporaryDirectory() as directory:
            Agent(model, LocalMCPTools(directory)).run_plan(plan)

    def test_rejects_tool_not_allowed_by_plan(self) -> None:
        tools = LocalMCPTools(".")
        with self.assertRaises(ToolError):
            tools.call_tool("echo", {"text": "hello"}, ())

    def test_read_text_cannot_escape_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory).parent / f"{Path(directory).name}-outside.txt"
            outside.write_text("not allowed", encoding="utf-8")
            tools = LocalMCPTools(directory)
            result = tools.call_tool(
                "read_text", {"path": f"../{outside.name}"}, ("read_text",)
            )
            self.assertTrue(result.is_error)
            outside.unlink()


if __name__ == "__main__":
    unittest.main()
