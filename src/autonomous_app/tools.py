from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .models import ToolResult


class ToolError(ValueError):
    """Raised when a tool request is invalid or not allow-listed."""


class LocalMCPTools:
    """Small in-process MCP-shaped provider for explicitly local tools."""

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).resolve()
        self._tools: dict[str, tuple[Callable[..., str], dict[str, Any]]] = {
            "echo": (
                self._echo,
                {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
            ),
            "read_text": (
                self._read_text,
                {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            ),
            "utc_time": (
                self._utc_time,
                {"type": "object", "properties": {}, "additionalProperties": False},
            ),
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "inputSchema": schema}
            for name, (_, schema) in self._tools.items()
        ]

    def call_tool(
        self, name: str, arguments: dict[str, Any], allowed_tools: tuple[str, ...]
    ) -> ToolResult:
        if name not in allowed_tools:
            raise ToolError(f"Tool '{name}' is not allowed by this plan.")
        if name not in self._tools:
            raise ToolError(f"Unknown local tool '{name}'.")
        handler, schema = self._tools[name]
        expected = set(schema["properties"])
        required = set(schema.get("required", []))
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be an object.")
        if set(arguments) - expected or required - set(arguments):
            raise ToolError(f"Invalid arguments for tool '{name}'.")
        for key, value in arguments.items():
            if schema["properties"][key]["type"] == "string" and not isinstance(value, str):
                raise ToolError(f"Argument '{key}' must be a string.")
        try:
            return ToolResult(handler(**arguments))
        except (OSError, ValueError) as exc:
            return ToolResult(str(exc), is_error=True)

    @staticmethod
    def _echo(text: str) -> str:
        return text

    def _read_text(self, path: str) -> str:
        target = (self.workspace / path).resolve(strict=True)
        try:
            target.relative_to(self.workspace)
        except ValueError as exc:
            raise ToolError("Requested file is outside the configured workspace.") from exc
        if not target.is_file():
            raise ToolError("Requested path is not a regular file.")
        if target.stat().st_size > 64 * 1024:
            raise ToolError("Requested file exceeds the 64 KiB read limit.")
        return target.read_text(encoding="utf-8")

    @staticmethod
    def _utc_time() -> str:
        return datetime.now(timezone.utc).isoformat()
