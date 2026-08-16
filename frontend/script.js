// TaskFlow frontend — talks to the real FastAPI backend (two-process run).
// Change this if your backend runs on a different host/port.
const API_BASE = "https://taskflow-backend-v3se.onrender.com";
const CACHE_KEY = "taskflow_tasks_cache";

const els = {
  projectInput: document.getElementById("project-select"),
  sortSelect: document.getElementById("sort-select"),
  searchInput: document.getElementById("search-input"),
  searchAlgo: document.getElementById("search-algo"),
  searchBtn: document.getElementById("search-btn"),
  clearSearchBtn: document.getElementById("clear-search-btn"),
  addForm: document.getElementById("add-task-form"),
  titleInput: document.getElementById("task-title"),
  dueDateInput: document.getElementById("task-due-date"),
  priorityInput: document.getElementById("task-priority"),
  titleError: document.getElementById("title-error"),
  quickAddForm: document.getElementById("quick-add-form"),
  quickAddInput: document.getElementById("quick-add-input"),
  statsContent: document.getElementById("stats-content"),
  listContainer: document.getElementById("task-list-container"),
};

let currentTasks = [];

// ---------------------------------------------------------------------
// Cache helpers (Task 14): cache task list in localStorage, render from
// cache first on load so the page never shows a blank list while the
// live request is in flight.
// ---------------------------------------------------------------------
function cacheTasks(tasks) {
  localStorage.setItem(CACHE_KEY, JSON.stringify(tasks));
}

function loadCachedTasks() {
  const raw = localStorage.getItem(CACHE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch (e) {
    return [];
  }
}

// ---------------------------------------------------------------------
// Rendering — built with createElement/appendChild, textContent for all
// user-provided values (no innerHTML string building from user input).
// ---------------------------------------------------------------------
function renderTasks(tasks) {
  els.listContainer.textContent = ""; // clear safely

  if (!tasks || tasks.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No tasks yet — add one above.";
    els.listContainer.appendChild(empty);
    return;
  }

  tasks.forEach((task) => {
    const item = document.createElement("div");
    item.className = "task-item";
    item.dataset.taskId = task.id;

    const main = document.createElement("div");
    main.className = "task-main";

    const badge = document.createElement("span");
    badge.className = `badge ${task.priority}`;
    badge.textContent = task.priority;

    const title = document.createElement("span");
    title.className = "task-title";
    title.textContent = task.title;

    main.appendChild(badge);
    main.appendChild(title);

    const meta = document.createElement("div");
    meta.className = "task-meta";
    meta.textContent = `status: ${task.status} | due: ${task.due_date || "—"} | project #${task.project_id}`;
    main.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "edit-btn";
    editBtn.textContent = "Edit";
    editBtn.addEventListener("click", () => handleEdit(task));

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "delete-btn";
    deleteBtn.textContent = "Delete";
    deleteBtn.addEventListener("click", () => handleDelete(task.id));

    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    item.appendChild(main);
    item.appendChild(actions);
    els.listContainer.appendChild(item);
  });
}

function renderStats(stats) {
  els.statsContent.textContent = "";
  if (!stats) {
    els.statsContent.textContent = "No stats available.";
    return;
  }
  const summary = document.createElement("p");
  summary.textContent = `${stats.project_name}: ${stats.task_count} task(s)`;
  els.statsContent.appendChild(summary);

  const breakdown = document.createElement("p");
  const parts = Object.entries(stats.by_status).map(([status, count]) => `${status}: ${count}`);
  breakdown.textContent = parts.length ? parts.join(" | ") : "No status breakdown yet.";
  els.statsContent.appendChild(breakdown);
}

// ---------------------------------------------------------------------
// Data loading
// ---------------------------------------------------------------------
async function loadTasks() {
  const projectId = els.projectInput.value;
  const sort = els.sortSelect.value;

  let url = `${API_BASE}/tasks?project_id=${encodeURIComponent(projectId)}`;
  if (sort) url += `&sort=${encodeURIComponent(sort)}`;

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to load tasks");
  const tasks = await response.json();
  currentTasks = tasks;
  cacheTasks(tasks);
  renderTasks(tasks);
}

async function loadStats() {
  const projectId = els.projectInput.value;
  try {
    const response = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectId)}/stats`);
    if (!response.ok) {
      renderStats(null);
      return;
    }
    const stats = await response.json();
    renderStats(stats);
  } catch (e) {
    renderStats(null);
  }
}

async function refreshAll() {
  try {
    await Promise.all([loadTasks(), loadStats()]);
  } catch (e) {
    console.error(e);
  }
}

// ---------------------------------------------------------------------
// Add task (Task 12/15): preventDefault + client-side validation.
// ---------------------------------------------------------------------
els.addForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const title = els.titleInput.value.trim();
  if (!title) {
    els.titleError.textContent = "Title is required.";
    return;
  }
  els.titleError.textContent = "";

  const payload = {
    title,
    priority: els.priorityInput.value,
    due_date: els.dueDateInput.value.trim() || null,
    project_id: parseInt(els.projectInput.value, 10),
  };

  try {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      els.titleInput.value = "";
      els.dueDateInput.value = "";
      await refreshAll();
    } else {
      const body = await response.json().catch(() => null);
      els.titleError.textContent = body?.detail
        ? `Could not add task — ${JSON.stringify(body.detail)}`
        : "Could not add task — check the fields.";
    }
  } catch (err) {
    // Network/CORS failures land here — fetch() throws before you ever
    // get a response, e.g. if the backend isn't running, or if this page
    // was opened via file:// / a port CORS doesn't allow.
    console.error("Add task request failed:", err);
    els.titleError.textContent =
  "Could not reach the backend — please check your internet connection or try again."  }
});

els.titleInput.addEventListener("input", () => {
  if (els.titleInput.value.trim()) {
    els.titleError.textContent = "";
  }
});

// ---------------------------------------------------------------------
// Quick-Add (Section 3)
// ---------------------------------------------------------------------
els.quickAddForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const description = els.quickAddInput.value.trim();
  if (!description) return;

  try {
    const response = await fetch(`${API_BASE}/tasks/quick-add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        description,
        project_id: parseInt(els.projectInput.value, 10),
      }),
    });

    if (response.ok) {
      els.quickAddInput.value = "";
      await refreshAll();
    } else {
      const body = await response.json().catch(() => null);
      alert(body?.detail ? `Quick-add failed — ${JSON.stringify(body.detail)}` : "Quick-add failed — check the project ID and description.");
    }
  } catch (err) {
    console.error("Quick-add request failed:", err);
    alert("Could not reach the backend — please check your internet connection or try again.");
  }
});

// ---------------------------------------------------------------------
// Edit / Delete
// ---------------------------------------------------------------------
async function handleEdit(task) {
  const newTitle = prompt("Edit title:", task.title);
  if (newTitle === null) return; // cancelled
  const trimmed = newTitle.trim();
  if (!trimmed) {
    alert("Title cannot be empty.");
    return;
  }

  const response = await fetch(`${API_BASE}/tasks/${task.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: trimmed }),
  });

  if (response.ok) {
    await refreshAll();
  } else {
    alert("Update failed.");
  }
}

async function handleDelete(taskId) {
  if (!confirm("Delete this task?")) return;
  const response = await fetch(`${API_BASE}/tasks/${taskId}`, { method: "DELETE" });
  if (response.ok) {
    await refreshAll();
  } else {
    alert("Delete failed.");
  }
}

// ---------------------------------------------------------------------
// Search (Section 2)
// ---------------------------------------------------------------------
els.searchBtn.addEventListener("click", async () => {
  const title = els.searchInput.value.trim();
  if (!title) return;
  const algo = els.searchAlgo.value;

  const response = await fetch(
    `${API_BASE}/tasks/search?title=${encodeURIComponent(title)}&algo=${encodeURIComponent(algo)}`
  );

  if (response.ok) {
    const task = await response.json();
    renderTasks([task]);
  } else {
    renderTasks([]);
  }
});

els.clearSearchBtn.addEventListener("click", async () => {
  els.searchInput.value = "";
  await refreshAll();
});

els.sortSelect.addEventListener("change", refreshAll);
els.projectInput.addEventListener("change", refreshAll);

// ---------------------------------------------------------------------
// Initial load: render cached copy immediately, then fetch live data.
// ---------------------------------------------------------------------
function init() {
  const cached = loadCachedTasks();
  if (cached.length) renderTasks(cached);
  refreshAll();
}

init();