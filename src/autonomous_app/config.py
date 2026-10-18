import json
from pathlib import Path
from typing import Any

from .models import Plan, Step


class ConfigurationError(ValueError):
    """Raised when a plan file is missing or invalid."""


def load_plan(path: str | Path) -> Plan:
    plan_path = Path(path)
    try:
        raw = _read_config(plan_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Unable to read plan at {plan_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigurationError("The plan document must be a mapping.")

    try:
        name = _required_string(raw, "name")
        interval_seconds = _positive_int(raw, "interval_seconds", minimum=0)
        max_iterations = _positive_int(raw, "max_iterations", minimum=1)
        allowed_tools = raw["allowed_tools"]
        steps_data = raw["steps"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(f"Invalid plan: {exc}") from exc

    if (
        not isinstance(allowed_tools, list)
        or not all(isinstance(tool, str) and tool for tool in allowed_tools)
    ):
        raise ConfigurationError("'allowed_tools' must be a list of non-empty names.")
    if len(set(allowed_tools)) != len(allowed_tools):
        raise ConfigurationError("'allowed_tools' must not contain duplicates.")
    if not isinstance(steps_data, list) or not steps_data:
        raise ConfigurationError("'steps' must be a non-empty list.")

    steps = []
    for index, item in enumerate(steps_data):
        if not isinstance(item, dict):
            raise ConfigurationError(f"Step {index} must be a mapping.")
        try:
            steps.append(Step(_required_string(item, "name"), _required_string(item, "prompt")))
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigurationError(f"Invalid step {index}: {exc}") from exc

    return Plan(
        name=name,
        interval_seconds=interval_seconds,
        max_iterations=max_iterations,
        allowed_tools=tuple(allowed_tools),
        steps=tuple(steps),
    )


def _read_config(path: Path) -> Any:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise ConfigurationError(
                "YAML support requires PyYAML. Install dependencies with "
                "'python -m pip install -r requirements.txt'."
            ) from exc
        return yaml.safe_load(text)
    raise ConfigurationError("Plan files must use .json, .yaml, or .yml.")


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' must be a non-empty string.")
    return value.strip()


def _positive_int(data: dict[str, Any], key: str, minimum: int) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"'{key}' must be an integer greater than or equal to {minimum}.")
    return value
