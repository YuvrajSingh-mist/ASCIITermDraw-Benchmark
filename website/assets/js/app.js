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

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function attachLightbox() {
  const overlay = document.getElementById("lightbox-overlay");
  const overlayImg = document.getElementById("lightbox-image");
  const closeBtn = overlay ? overlay.querySelector(".lightbox-close") : null;
  if (!overlay || !overlayImg) {
    return;
  }

  function open(img) {
    overlayImg.src = img.src;
    overlayImg.alt = img.alt;
    overlay.classList.add("active");
    overlay.setAttribute("aria-hidden", "false");
  }

  function close() {
    overlay.classList.remove("active");
    overlay.setAttribute("aria-hidden", "true");
    overlayImg.src = "";
  }

  for (const img of document.querySelectorAll("img.lightbox-trigger")) {
    img.addEventListener("click", () => open(img));
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", close);
  }
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      close();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && overlay.classList.contains("active")) {
      close();
    }
  });
}

function assetsBasePath() {
  const dataPath = document.body.dataset.siteData || "./assets/data/site_data.json";
  return dataPath.replace("assets/data/site_data.json", "assets/");
}

function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function publicExampleMarkup(example, base) {
  return `
    <article class="public-example">
      <div class="public-example-meta">
        <span class="public-example-cat">${example.category_name} <span class="public-example-id">${example.task_id}</span></span>
        <span class="public-example-diff">${capitalize(example.difficulty)}${example.has_source ? "  -  image-conditioned edit" : ""}</span>
      </div>
      <pre class="public-example-prompt"><code>${escapeHtml(example.prompt)}</code></pre>
      <img
        class="public-example-img lightbox-trigger"
        src="${base}${example.img}"
        alt="${escapeHtml(example.category_name)} — ${example.difficulty} example diagram"
        loading="lazy"
      />
    </article>
  `;
}

// Renders a list of public_examples into any container using the same card
// markup/styling, so the homepage's featured examples and the Tasks page's
// full example list look identical apart from which examples are included.
function renderPublicExampleList(containerId, examples) {
  const root = document.getElementById(containerId);
  if (!root || !examples) {
    return;
  }
  const base = assetsBasePath();
  root.innerHTML = examples.map((example) => publicExampleMarkup(example, base)).join("");
}

loadData()
  .then((data) => {
    renderStatsInline(data.stats);
    renderCategoryTable(data.categories);
    renderBenchmarkSummary(data.categories);
    renderPublicExampleList(
      "featured-examples-list",
      (data.public_examples || []).filter((example) => example.difficulty === "hard")
    );
    renderPublicExampleList("public-examples-list", data.public_examples);
    attachLightbox();
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
