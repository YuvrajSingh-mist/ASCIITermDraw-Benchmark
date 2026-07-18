async function loadData() {
  const dataPath = document.body.dataset.siteData || "./assets/data/site_data.json";
  const response = await fetch(dataPath);
  if (!response.ok) {
    throw new Error("Failed to load site data");
  }
  return response.json();
}

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

function renderBenchmarkSummary(categories) {
  const root = document.getElementById("benchmark-summary-body");
  if (!root) {
    return;
  }
  root.innerHTML = categories
    .map((category) => {
      const counts = category.difficulty || { easy: 0, medium: 0, hard: 0 };
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

loadData()
  .then((data) => {
    renderStatsInline(data.stats);
    renderCategoryTable(data.categories);
    renderBenchmarkSummary(data.categories);
  })
  .catch((error) => {
    const statsRoot = document.getElementById("stats-inline");
    const summaryRoot = document.getElementById("benchmark-summary-body");
    if (statsRoot) {
      statsRoot.textContent = error.message;
    }
    if (summaryRoot) {
      summaryRoot.innerHTML = `<tr><td colspan="3">${error.message}</td></tr>`;
    }
  });
