import json
import os
import subprocess
from pathlib import Path


PLAN_FILE = Path(
    os.path.expanduser(os.environ.get("APKA_PLAN_FILE", "~/config/current_plan.json"))
)
ROOT = Path(__file__).resolve().parents[2]


def load_plan() -> dict:
    if not PLAN_FILE.exists():
        return {"tasks": [], "status": "Brak aktywnego planu"}
    with PLAN_FILE.open("r", encoding="utf-8") as plan_file:
        plan = json.load(plan_file)
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks", []), list):
        raise ValueError("Plan musi być obiektem JSON zawierającym tablicę 'tasks'.")
    return plan


def save_plan(plan: dict) -> None:
    temporary_file = PLAN_FILE.with_name(f"{PLAN_FILE.name}.{os.getpid()}.tmp")
    with temporary_file.open("w", encoding="utf-8") as plan_file:
        json.dump(plan, plan_file, ensure_ascii=False, indent=2)
        plan_file.write("\n")
    temporary_file.replace(PLAN_FILE)


def execute_agent_loop() -> None:
    print("[agent] Uruchamianie pętli agenta i weryfikacja planu...")
    plan = load_plan()
    if not PLAN_FILE.exists():
        print(plan["status"])
        return

    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            raise ValueError("Każde zadanie w planie musi być obiektem JSON.")
        if task.get("completed", False):
            continue
        print(f"-> Wykonywanie zadania: {task.get('name', '(bez nazwy)')}")
        result = subprocess.run(
            ["node", str(ROOT / "index.js"), "--task-stdin"],
            input=json.dumps(task, ensure_ascii=False),
            text=True,
            cwd=ROOT,
            check=False,
            shell=False,
        )
        if result.returncode:
            raise RuntimeError("Wykonanie zadania przez Copilot SDK nie powiodło się.")
        task["completed"] = True
        save_plan(plan)

    plan["status"] = "Cykl planu zakończony pomyślnie."
    save_plan(plan)
    print("Cykl planu zakończony pomyślnie.")
