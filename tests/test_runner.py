import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autonomous_app import current_plan as runner


class CurrentPlanTests(unittest.TestCase):
    def test_missing_plan_returns_empty_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runner, "PLAN_FILE", Path(directory) / "missing.json"):
                self.assertEqual(
                    runner.load_plan(),
                    {"tasks": [], "status": "Brak aktywnego planu"},
                )

    def test_successful_task_is_persisted_as_completed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan_file = Path(directory) / "current_plan.json"
            plan_file.write_text(
                json.dumps(
                    {"status": "Aktywny plan", "tasks": [{"name": "test", "completed": False}]}
                ),
                encoding="utf-8",
            )
            with (
                patch.object(runner, "PLAN_FILE", plan_file),
                patch.object(runner.subprocess, "run") as run,
            ):
                run.return_value.returncode = 0
                runner.execute_agent_loop()

            saved = json.loads(plan_file.read_text(encoding="utf-8"))
            self.assertTrue(saved["tasks"][0]["completed"])
            self.assertEqual(saved["status"], "Cykl planu zakończony pomyślnie.")


if __name__ == "__main__":
    unittest.main()
