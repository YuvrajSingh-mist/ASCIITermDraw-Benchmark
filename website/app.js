async function loadData() {
  const response = await fetch("./site_data.json");
  if (!response.ok) {
    throw new Error("Failed to load site data");
  }
  return response.json();
}

function renderStatsInline(stats) {
  const root = document.getElementById("stats-inline");
  root.textContent =
    `${stats.task_count} tasks across ${stats.category_count} categories, ` +
    `${stats.edit_task_count} image-conditioned edit tasks, and ` +
    `${stats.rendered_reference_count} rendered references.`;
}

function renderCategoryTable(categories) {
  const root = document.getElementById("category-table-body");
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

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderFeaturedTasks(categories) {
  const root = document.getElementById("featured-task-grid");
  const featured = categories
    .map((category) => ({ category, task: category.tasks[0] }))
    .filter((entry) => entry.task);

  root.innerHTML = featured
    .map(
      ({ category, task }) => `
        <article class="task-card">
          <div class="task-card-header">
            <span class="task-card-id">${task.task_id}</span>
            <span class="task-meta">${category.name}</span>
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
  return `
    <article class="task-item" data-search="${[
      task.task_id,
      task.title,
      task.prompt,
      category.name,
      category.slug,
    ]
      .join(" ")
      .toLowerCase()}">
      <div class="task-head">
        <span class="task-id">${task.task_id}</span>
        <span class="task-title">${task.title}</span>
      </div>
      <div class="task-meta">
        ${category.name}  -  ${task.path}${task.has_source ? "  -  image-conditioned edit" : ""}
      </div>
      <div class="task-prompt">${task.prompt}</div>
      <pre><code>${escapeHtml(task.preview)}</code></pre>
    </article>
  `;
}

function renderTasks(categories) {
  const root = document.getElementById("task-list");
  root.innerHTML = categories
    .flatMap((category) => category.tasks.map((task) => taskMarkup(task, category)))
    .join("");
}

function attachFilter() {
  const input = document.getElementById("task-filter");
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
    renderFeaturedTasks(data.categories);
    renderTasks(data.categories);
    attachFilter();
  })
  .catch((error) => {
    const statsRoot = document.getElementById("stats-inline");
    const taskRoot = document.getElementById("task-list");
    if (statsRoot) {
      statsRoot.textContent = error.message;
    }
    if (taskRoot) {
      taskRoot.innerHTML = `<article class="task-item"><div class="task-prompt">${error.message}</div></article>`;
    }
  });
