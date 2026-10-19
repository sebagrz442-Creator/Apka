import json
import os
import shutil
import subprocess
from typing import Any

from .models import Step, ToolAction


class CopilotError(RuntimeError):
    """Raised when the Copilot CLI is unavailable or returns invalid output."""


class CopilotCLI:
    def __init__(self, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = timeout_seconds

    def next_action(self, step: Step, history: list[dict[str, Any]]) -> ToolAction | None:
        if os.environ.get("APKA_ALLOW_MODEL_ACCESS") != "1":
            raise CopilotError(
                "Model access is disabled. Set APKA_ALLOW_MODEL_ACCESS=1 only "
                "after reviewing the data sent to Copilot."
            )

        executable = shutil.which("copilot")
        if not executable:
            raise CopilotError("Copilot CLI was not found on PATH.")

        prompt = (
            "You are an automation planner. Choose exactly one next tool action "
            "from the tools listed below, or finish if the task is complete. "
            "Return only JSON: {\"tool\":\"name\",\"arguments\":{...}} or "
            "{\"done\":true}. Do not include markdown.\n"
            f"Task: {step.prompt}\n"
            f"History: {json.dumps(history, ensure_ascii=False)}"
        )
        try:
            result = subprocess.run(
                [executable, "-p", prompt],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CopilotError(f"Copilot CLI invocation failed: {exc}") from exc
        if result.returncode != 0:
            raise CopilotError(f"Copilot CLI exited with status {result.returncode}.")

        try:
            response = json.loads(result.stdout.strip())
        except json.JSONDecodeError as exc:
            raise CopilotError("Copilot CLI did not return valid JSON.") from exc
        if not isinstance(response, dict):
            raise CopilotError("Copilot response must be a JSON object.")
        if response.get("done") is True:
            return None

        tool = response.get("tool")
        arguments = response.get("arguments", {})
        if not isinstance(tool, str) or not tool:
            raise CopilotError("Copilot response must include a non-empty 'tool'.")
        if not isinstance(arguments, dict):
            raise CopilotError("'arguments' in the Copilot response must be an object.")
        return ToolAction(tool=tool, arguments=arguments)
