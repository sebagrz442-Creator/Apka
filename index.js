import { CopilotClient, defineTool } from "@github/copilot-sdk";
import { access, readFile, realpath, rename, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const planFile = path.resolve(
  process.env.APKA_PLAN_FILE ?? path.join(os.homedir(), "config", "current_plan.json"),
);
const workspace = await realpath(process.cwd());

function requireOptIn() {
  if (
    process.env.APKA_ENABLE_COPILOT !== "1" ||
    process.env.APKA_ALLOW_MODEL_ACCESS !== "1"
  ) {
    throw new Error(
      "Copilot access is disabled. Set APKA_ENABLE_COPILOT=1 and " +
        "APKA_ALLOW_MODEL_ACCESS=1 after reviewing the data shared with Copilot.",
    );
  }
}

async function loadPlan() {
  try {
    return JSON.parse(await readFile(planFile, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      return { tasks: [], status: "Brak aktywnego planu" };
    }
    throw error;
  }
}

async function savePlan(plan) {
  const temporaryFile = `${planFile}.${process.pid}.tmp`;
  await writeFile(temporaryFile, `${JSON.stringify(plan, null, 2)}\n`, {
    encoding: "utf8",
    mode: 0o600,
  });
  await rename(temporaryFile, planFile);
}

function localTools(task) {
  const allowlist = new Set(Array.isArray(task.allowed_tools) ? task.allowed_tools : []);
  const tools = [];
  if (allowlist.has("echo")) {
    tools.push(
      defineTool("echo", {
        description: "Return the supplied text without changing it.",
        parameters: {
          type: "object",
          properties: { text: { type: "string" } },
          required: ["text"],
          additionalProperties: false,
        },
        handler: ({ text }) => text,
      }),
    );
  }
  if (allowlist.has("read_text")) {
    tools.push(
      defineTool("read_text", {
        description: "Read a UTF-8 text file inside the current workspace (up to 64 KiB).",
        parameters: {
          type: "object",
          properties: { path: { type: "string" } },
          required: ["path"],
          additionalProperties: false,
        },
        handler: async ({ path: requestedPath }) => {
          const candidate = path.resolve(workspace, requestedPath);
          const resolved = await realpath(candidate);
          const relative = path.relative(workspace, resolved);
          if (
            relative === ".." ||
            relative.startsWith(`..${path.sep}`) ||
            path.isAbsolute(relative)
          ) {
            throw new Error("Requested file is outside the configured workspace.");
          }
          const details = await stat(resolved);
          if (!details.isFile() || details.size > 64 * 1024) {
            throw new Error("Requested path must be a file no larger than 64 KiB.");
          }
          return readFile(resolved, "utf8");
        },
      }),
    );
  }
  return tools;
}

async function askCopilot(task) {
  requireOptIn();
  const client = new CopilotClient({ mode: "empty", workingDirectory: workspace });
  await client.start();
  let session;
  try {
    session = await client.createSession({ tools: localTools(task) });
    const reply = new Promise((resolve, reject) => {
      let content = "";
      const timeout = setTimeout(
        () => reject(new Error("Copilot response timed out.")),
        120_000,
      );
      session.on("assistant.message", (event) => {
        content = event.data.content;
      });
      session.on("session.idle", () => {
        clearTimeout(timeout);
        resolve(content);
      });
    });
    await session.send({
      prompt:
        `Complete this task using only explicitly provided local tools. ` +
        `Do not claim an action was taken unless it was performed.\n` +
        `Task: ${String(task.prompt ?? task.name ?? "")}`,
    });
    const answer = await reply;
    console.log(answer);
  } finally {
    if (session) await session.disconnect();
    await client.stop();
  }
}

async function runPlan() {
  const plan = await loadPlan();
  try {
    await access(planFile);
  } catch (error) {
    if (error.code === "ENOENT") {
      console.log(plan.status);
      return;
    }
    throw error;
  }
  if (!Array.isArray(plan.tasks)) {
    throw new Error("Plan 'tasks' must be an array.");
  }
  for (const task of plan.tasks) {
    if (task?.completed === true) continue;
    if (!task || typeof task !== "object") {
      throw new Error("Every plan task must be an object.");
    }
    console.log(`-> Wykonywanie zadania: ${task.name ?? "(bez nazwy)"}`);
    await askCopilot(task);
    task.completed = true;
    await savePlan(plan);
  }
  plan.status = "Cykl planu zakończony pomyślnie.";
  await savePlan(plan);
  console.log("Cykl planu zakończony pomyślnie.");
}

async function main() {
  const taskIndex = process.argv.indexOf("--task-stdin");
  if (taskIndex !== -1) {
    let input = "";
    for await (const chunk of process.stdin) input += chunk;
    const task = JSON.parse(input);
    if (!task || typeof task !== "object" || Array.isArray(task)) {
      throw new Error("Task input must be a JSON object.");
    }
    await askCopilot(task);
    return;
  }
  await runPlan();
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
});
