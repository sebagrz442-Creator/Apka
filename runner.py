import argparse
import os
import sys
import time
from pathlib import Path

from autonomous_app.agent import Agent
from autonomous_app.config import ConfigurationError, load_plan
from autonomous_app.copilot import CopilotCLI, CopilotError
from autonomous_app.tools import LocalMCPTools


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Copilot automation plan.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/sample.json"),
        help="Path to a JSON or YAML plan file.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the plan once instead of repeating at its configured interval.",
    )
    args = parser.parse_args()

    if os.environ.get("APKA_ENABLE_COPILOT") != "1":
        print(
            "Copilot is disabled. Set APKA_ENABLE_COPILOT=1 and "
            "APKA_ALLOW_MODEL_ACCESS=1 to enable model access.",
            file=sys.stderr,
        )
        return 2

    try:
        plan = load_plan(args.config)
        agent = Agent(CopilotCLI(), LocalMCPTools(Path.cwd()))
        while True:
            agent.run_plan(plan)
            if args.once:
                break
            time.sleep(plan.interval_seconds)
    except (ConfigurationError, CopilotError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
