# Autonomous App Builder

A small, local-first agent app with a Python plan runner and a Node.js Copilot
SDK worker. It reads JSON/YAML plans and dispatches only explicitly allow-listed
local tools. `LocalMCPTools` exposes an in-process MCP-shaped
`list_tools`/`call_tool` interface; the SDK worker provides bounded local
`read_text` and `echo` tools. No network-capable tool or file-writing tool is
enabled by default.

## Run

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
npm install
export APKA_ENABLE_COPILOT=1
export APKA_ALLOW_MODEL_ACCESS=1
npm start
```

`npm start` runs the Copilot SDK against `~/config/current_plan.json`. The
Python task runner (`npm run agent:run`) uses that same plan and delegates each
unfinished task to the SDK worker. Set `APKA_PLAN_FILE` to use another path.
Copy `config/current_plan.example.json` to `~/config/current_plan.json` to get
started. `python runner.py --config config/sample.yaml --once` runs the
standalone Python/Copilot CLI plan runner instead.

## Local dashboard

Run the static dashboard without installing additional packages:

```sh
python3 -m http.server 8000 --directory dashboard
```

Open `http://localhost:8000` on the same device. It starts with local sample
data; use **Wczytaj plan JSON** to select an existing `current_plan.json`.
Imported plans are read in the browser and are not uploaded or saved by the
dashboard. The dashboard summarizes task completion and allowed tools, and
uses prompt character count as a lightweight complexity proxy.

Model access is opt-in:
task prompts, tool arguments, and returned local file contents may be sent to
Copilot. Review the plan and data before enabling it. The CLI is launched without
a shell, and its output cannot invoke tools outside the plan allow-list. Keep
plans and workspaces free of secrets. Only use `read_text` for files you intend
to provide to the model.

Omit `--once` to repeat the Python plan after the configured `interval_seconds`. Use
`--config` to select another JSON/YAML plan. Plans set a per-step
`max_iterations` limit to bound tool use. YAML parsing uses `yaml.safe_load`.

## Layout

- `src/autonomous_app/`: configuration, agent loop, Copilot CLI adapter, and local tools
- `config/`: sample JSON and YAML plans
- `tests/`: standard-library unit tests
- `runner.py`: command-line entry points for the Python plan runner

The in-process tool provider is an MCP-shaped starting point, not a wire-protocol
MCP client. Connect a local MCP server through a dedicated provider adapter
before enabling external tools; configure that adapter to use explicitly
approved local processes only.

## Tests

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
