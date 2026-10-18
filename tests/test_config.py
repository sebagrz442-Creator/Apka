import json
import tempfile
import unittest
from pathlib import Path

from autonomous_app.config import ConfigurationError, load_plan


class LoadPlanTests(unittest.TestCase):
    def test_loads_json_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(
                json.dumps(
                    {
                        "name": "test",
                        "interval_seconds": 0,
                        "max_iterations": 2,
                        "allowed_tools": ["echo"],
                        "steps": [{"name": "step", "prompt": "do work"}],
                    }
                ),
                encoding="utf-8",
            )
            plan = load_plan(path)
        self.assertEqual(plan.name, "test")
        self.assertEqual(plan.steps[0].prompt, "do work")

    def test_rejects_invalid_iteration_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(
                '{"name":"test","interval_seconds":0,"max_iterations":0,'
                '"allowed_tools":[],"steps":[{"name":"step","prompt":"work"}]}',
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError):
                load_plan(path)

    def test_loads_yaml_plan_when_dependency_is_available(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML is not installed.")
        plan = load_plan(Path(__file__).parents[1] / "config" / "sample.yaml")
        self.assertEqual(plan.name, "local-example")
