import sys

from autonomous_app.current_plan import execute_agent_loop


if __name__ == "__main__":
    try:
        execute_agent_loop()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        raise SystemExit(1) from error
