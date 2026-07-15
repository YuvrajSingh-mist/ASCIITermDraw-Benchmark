async function loadData() {
  const dataPath = document.body.dataset.siteData || "./assets/data/site_data.json";
  const response = await fetch(dataPath);
  if (!response.ok) {
    throw new Error("Failed to load site data");
  }
  return response.json();
}

const FEATURED_TASK_IDS = {
  "box-layout-basics": "1.10",
  "network-topology-diagrams": "2.17",
  "diagram-editing": "3.16",
  "software-architecture-diagrams": "4.14",
};

function renderStatsInline(stats) {
  const root = document.getElementById("stats-inline");
  if (!root) {
    return;
  }
  root.textContent =
    `${stats.task_count} tasks across ${stats.category_count} categories, ` +
    `${stats.edit_task_count} image-conditioned edit tasks, and ` +
    `${stats.rendered_reference_count} rendered references.`;
}

function renderCategoryTable(categories) {
  const root = document.getElementById("category-table-body");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .map(
      (category) => `
        <tr>
          <td>${category.name} (${category.count})</td>
          <td>${category.description}</td>
        </tr>
      `
    )
    .join("");
}

function difficultyCounts(tasks) {
  const counts = { easy: 0, medium: 0, hard: 0 };
  for (const task of tasks) {
    if (task.path.includes("/easy/")) counts.easy += 1;
    if (task.path.includes("/medium/")) counts.medium += 1;
    if (task.path.includes("/hard/")) counts.hard += 1;
  }
  return counts;
}

function renderBenchmarkSummary(categories) {
  const root = document.getElementById("benchmark-summary-body");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .map((category) => {
      const counts = difficultyCounts(category.tasks);
      return `
        <tr>
          <td>${category.name}</td>
          <td>${category.count}</td>
          <td>Easy ${counts.easy}  -  Medium ${counts.medium}  -  Hard ${counts.hard}</td>
        </tr>
      `;
    })
    .join("");
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function difficultyLabel(task) {
  if (task.path.includes("/easy/")) return "Easy";
  if (task.path.includes("/medium/")) return "Medium";
  return "Hard";
}

function renderFeaturedTasks(categories) {
  const root = document.getElementById("featured-task-grid");
  if (!root) {
    return;
  }
  const featured = categories
    .map((category) => ({
      category,
      task:
        category.tasks.find(
          (task) => task.task_id === FEATURED_TASK_IDS[category.slug]
        ) || category.tasks[0],
    }))
    .filter((entry) => entry.task);

  root.innerHTML = featured
    .map(
      ({ category, task }) => `
        <article class="task-card">
          <div class="task-card-header">
            <span class="task-card-id">${task.task_id}</span>
            <span class="task-meta">${category.name}  -  ${difficultyLabel(task)}</span>
          </div>
          <h3>${task.title}</h3>
          <p>${task.prompt}</p>
          <pre><code>${escapeHtml(task.preview)}</code></pre>
        </article>
      `
    )
    .join("");
}

function taskMarkup(task, category) {
  const difficulty = difficultyLabel(task);
  return `
    <article class="task-item" data-search="${[
      task.task_id,
      task.title,
      task.prompt,
      category.name,
      category.slug,
      difficulty,
      task.path,
    ]
      .join(" ")
      .toLowerCase()}">
      <div class="task-head">
        <span class="task-id">${task.task_id}</span>
        <span class="task-title">${task.title}</span>
      </div>
      <div class="task-meta">
        ${category.name}  -  ${difficulty}  -  ${task.path}${task.has_source ? "  -  image-conditioned edit" : ""}
      </div>
      <div class="task-prompt">${task.prompt}</div>
      <pre><code>${escapeHtml(task.preview)}</code></pre>
    </article>
  `;
}

function renderTasks(categories) {
  const root = document.getElementById("task-list");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .flatMap((category) => category.tasks.map((task) => taskMarkup(task, category)))
    .join("");
}

function attachFilter() {
  const input = document.getElementById("task-filter");
  if (!input) {
    return;
  }
  const items = [...document.querySelectorAll(".task-item")];
  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    for (const item of items) {
      item.style.display = !query || item.dataset.search.includes(query) ? "" : "none";
    }
  });
}

loadData()
  .then((data) => {
    renderStatsInline(data.stats);
    renderCategoryTable(data.categories);
    renderBenchmarkSummary(data.categories);
    renderFeaturedTasks(data.categories);
    renderTasks(data.categories);
    attachFilter();
  })
  .catch((error) => {
    const statsRoot = document.getElementById("stats-inline");
    const taskRoot = document.getElementById("task-list");
    const summaryRoot = document.getElementById("benchmark-summary-body");
    if (statsRoot) {
      statsRoot.textContent = error.message;
    }
    if (summaryRoot) {
      summaryRoot.innerHTML = `<tr><td colspan="3">${error.message}</td></tr>`;
    }
    if (taskRoot) {
      taskRoot.innerHTML = `<article class="task-item"><div class="task-prompt">${error.message}</div></article>`;
    }
  });
