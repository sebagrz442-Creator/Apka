# Autonomous App Builder

A small, local-first Python agent loop that reads a JSON or YAML plan, asks the
Copilot CLI for one structured action at a time, and dispatches only explicitly
allow-listed tools. `LocalMCPTools` exposes a small in-process MCP-shaped
`list_tools`/`call_tool` interface with `echo`, bounded `read_text`, and `utc_time`.
No network-capable tool or file-writing tool is enabled by default.

## Run

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export APKA_ENABLE_COPILOT=1
export APKA_ALLOW_MODEL_ACCESS=1
python runner.py --config config/sample.yaml --once
```

Install and authenticate the Copilot CLI separately. Model access is opt-in:
task prompts, tool arguments, and returned local file contents may be sent to
Copilot. Review the plan and data before enabling it. The CLI is launched without
a shell, and its output cannot invoke tools outside the plan allow-list. Keep
plans and workspaces free of secrets. Only use `read_text` for files you intend
to provide to the model.

Omit `--once` to repeat the plan after the configured `interval_seconds`. Use
`--config` to select another JSON/YAML plan. Plans set a per-step
`max_iterations` limit to bound tool use. YAML parsing uses `yaml.safe_load`.

## Layout

- `src/autonomous_app/`: configuration, agent loop, Copilot CLI adapter, and local tools
- `config/`: sample JSON and YAML plans
- `tests/`: standard-library unit tests
- `runner.py`: command-line entry point

The in-process tool provider is an MCP-shaped starting point, not a wire-protocol
MCP client. Connect a local MCP server through a dedicated provider adapter
before enabling external tools; configure that adapter to use explicitly
approved local processes only.

## Tests

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
