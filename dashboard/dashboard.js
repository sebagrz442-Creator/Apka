const samplePlan = {
  version: "1.0",
  agent: {
    name: "System-Agent",
    description: "Agent wspierający rozwój aplikacji lokalnych i skryptów automatyzacji.",
    instructions:
      "Przestrzegaj zasad bezpieczeństwa, pełnej modularności kodu w Pythonie oraz unikaj wysyłania wrażliwych danych na zewnętrzne serwery. Zawsze dbaj o optymalizację pod kątem urządzeń mobilnych i środowiska Termux.",
  },
  status: "Aktywny plan",
  tasks: [
    { name: "Przejrzyj strukturę projektu", prompt: "Odczytaj README.md i podsumuj strukturę projektu oraz najważniejsze moduły.", allowed_tools: ["read_text"], completed: true },
    { name: "Sprawdź konfigurację", prompt: "Przeanalizuj pliki konfiguracyjne projektu pod kątem lokalnych ustawień oraz zależności.", allowed_tools: ["read_text"], completed: true },
    { name: "Zaproponuj podział modułów", prompt: "Przygotuj modularny podział kodu Python dla lokalnego agenta, uwzględniając testowalność i obsługę błędów.", allowed_tools: ["read_text", "echo"], completed: false },
    { name: "Zweryfikuj bezpieczeństwo planu", prompt: "Sprawdź, czy plan nie wysyła wrażliwych danych na zewnętrzne serwery i korzysta wyłącznie z jawnie dozwolonych narzędzi.", allowed_tools: ["read_text"], completed: false },
    { name: "Przygotuj testy", prompt: "Dodaj testy jednostkowe dla przetwarzania planu i sprawdź scenariusze brzegowe, w tym pustą listę zadań oraz brakujące pola.", allowed_tools: ["read_text", "echo"], completed: false },
  ],
};

const byId = (id) => document.getElementById(id);
let plan = samplePlan;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function renderBarChart(container, values, formatter = (value) => value) {
  if (!values.length) {
    container.innerHTML = '<p class="empty">Brak danych do wyświetlenia.</p>';
    return;
  }
  const maximum = Math.max(1, ...values.map((item) => item.value));
  container.innerHTML = values.map(({ label, value }) => `
    <div class="bar-row">
      <span class="bar-label" title="${escapeHtml(label)}">${escapeHtml(label)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.max(value ? 2 : 0, value / maximum * 100)}%"></div></div>
      <span class="bar-value">${formatter(value)}</span>
    </div>`).join("");
}

function validTasks(value) {
  if (!value || typeof value !== "object" || !Array.isArray(value.tasks)) {
    throw new Error("Plik musi zawierać tablicę zadań „tasks”.");
  }
  if (!value.tasks.every((task) => task && typeof task === "object" && !Array.isArray(task))) {
    throw new Error("Każde zadanie musi być obiektem JSON.");
  }
  return value;
}

function render() {
  const tasks = plan.tasks;
  const completed = tasks.filter((task) => task.completed === true).length;
  const rate = tasks.length ? Math.round(completed / tasks.length * 100) : 0;
  const toolCounts = new Map();
  for (const task of tasks) {
    const tools = Array.isArray(task.allowed_tools) ? task.allowed_tools : [];
    for (const tool of new Set(tools.filter((item) => typeof item === "string"))) {
      toolCounts.set(tool, (toolCounts.get(tool) || 0) + 1);
    }
  }

  byId("agent-name").textContent = plan.agent?.name || "Agent";
  byId("agent-description").textContent = plan.agent?.description || "Brak opisu agenta w tym planie.";
  byId("agent-instructions").textContent = plan.agent?.instructions || "Brak instrukcji agenta w tym planie.";
  byId("plan-status").textContent = plan.status || "Brak statusu planu";
  byId("plan-version").textContent = plan.version || "—";
  byId("total-tasks").textContent = tasks.length;
  byId("completed-tasks").textContent = completed;
  byId("completion-rate").textContent = `${rate}%`;
  byId("tool-count").textContent = toolCounts.size;
  byId("ring-rate").textContent = `${rate}%`;
  byId("legend-completed").textContent = completed;
  byId("legend-pending").textContent = tasks.length - completed;
  byId("completion-ring").style.background = `conic-gradient(var(--accent) ${rate * 3.6}deg, #334650 ${rate * 3.6}deg)`;
  byId("completion-ring").setAttribute("aria-label", `${rate}% zadań ukończonych`);

  renderBarChart(byId("tool-chart"), [...toolCounts].map(([label, value]) => ({ label, value })));
  renderBarChart(byId("prompt-chart"), tasks.map((task, index) => ({
    label: task.name || `Zadanie ${index + 1}`,
    value: typeof task.prompt === "string" ? task.prompt.length : 0,
  })), (value) => `${value} zn.`);

  const filter = byId("task-filter").value;
  const visibleTasks = tasks.filter((task) => filter === "all" || (filter === "completed") === (task.completed === true));
  byId("task-rows").innerHTML = visibleTasks.length ? visibleTasks.map((task, index) => {
    const name = task.name || `Zadanie ${index + 1}`;
    const prompt = typeof task.prompt === "string" ? task.prompt : "";
    const tools = Array.isArray(task.allowed_tools) ? task.allowed_tools.filter((item) => typeof item === "string") : [];
    const status = task.completed === true;
    return `<tr>
      <td class="task-name">${escapeHtml(name)}${prompt ? `<small title="${escapeHtml(prompt)}">${escapeHtml(prompt)}</small>` : ""}</td>
      <td><span class="badge${status ? "" : " pending"}">${status ? "Ukończone" : "Oczekujące"}</span></td>
      <td class="tools">${tools.length ? tools.map(escapeHtml).join(", ") : "—"}</td>
      <td>${prompt.length} zn.</td>
    </tr>`;
  }).join("") : '<tr><td colspan="4" class="empty">Brak zadań dla wybranego filtra.</td></tr>';
}

byId("task-filter").addEventListener("change", render);
byId("plan-file").addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  try {
    plan = validTasks(JSON.parse(await file.text()));
    byId("notice").textContent = "";
    byId("task-filter").value = "all";
    render();
  } catch (error) {
    byId("notice").textContent = `Nie udało się wczytać planu: ${error.message}`;
  } finally {
    event.target.value = "";
  }
});

render();
