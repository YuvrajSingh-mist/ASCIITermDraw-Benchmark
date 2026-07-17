// Leaderboard page. Real results, sourced from outputs/qwen3p7-plus/metrics.json
// and outputs/qwen3p7-plus/manifest.json (both gitignored/private, so the
// numbers are hand-copied here rather than fetched at build time). Update
// these constants -- and add another entry to LEADERBOARD_ROWS -- whenever a
// new model's results are published.
//
// qwen3p7-plus, 80 tasks, num_judgments=5 (see outputs/qwen3p7-plus/results.csv):
//   combined.mean = 1.3425 / max_possible 2.0 -> 67.1%
//   generation_cost_usd (Fireworks, all 80 tasks) = 0.058589

const LEADERBOARD_ROWS = [
  {
    rank: "1st",
    model: "qwen3p7-plus",
    org: "Alibaba (via Fireworks)",
    score: 67.1,
    price: 0.058589,
  },
];

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr><th>Rank</th><th>Model</th><th>Score (AVG@5)</th><th>Organization</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr class="${row.rank === "1st" ? "lb-row-rank1" : ""}">
                <td class="lb-rank">${row.rank}</td>
                <td>${row.model}</td>
                <td>${row.score.toFixed(1)}%</td>
                <td>${row.org}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function makeTooltip(card) {
  const tooltip = document.createElement("div");
  tooltip.className = "lb-tooltip";
  card.style.position = "relative";
  card.appendChild(tooltip);
  return tooltip;
}

function showTooltip(tooltip, x, y, html) {
  tooltip.innerHTML = html;
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
  tooltip.classList.add("active");
}

function hideTooltip(tooltip) {
  tooltip.classList.remove("active");
}

function renderPerfDollarChart() {
  const card = document.getElementById("perf-dollar-chart");
  const width = 760;
  const height = 360;
  const margin = { top: 16, right: 16, bottom: 44, left: 44 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const xMin = Math.log10(0.01);
  const xMax = Math.log10(1);
  const yMin = 0;
  const yMax = 100;

  const xScale = (price) => margin.left + ((Math.log10(price) - xMin) / (xMax - xMin)) * plotW;
  const yScale = (score) => margin.top + plotH - ((score - yMin) / (yMax - yMin)) * plotH;

  const xTicks = [0.01, 0.03, 0.1, 0.3, 1];
  const yTicks = [0, 25, 50, 75, 100];

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Score versus Fireworks generation cost per full benchmark run">`;

  for (const t of yTicks) {
    const y = yScale(t);
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${t}%</text>`;
  }
  for (const t of xTicks) {
    const x = xScale(t);
    svg += `<text class="lb-tick-label" x="${x}" y="${height - margin.bottom + 16}" text-anchor="middle">$${t}</text>`;
  }
  svg += `<text class="lb-axis-label" x="${margin.left + plotW / 2}" y="${height - 6}" text-anchor="middle">$ per full benchmark run, generation only (log) &nbsp;&middot;&nbsp; cheaper &#8592; &#8594; more expensive</text>`;
  svg += `<text class="lb-axis-label" transform="translate(12 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">Score (%)</text>`;

  for (const row of LEADERBOARD_ROWS) {
    const cx = xScale(row.price);
    const cy = yScale(row.score);
    svg += `<circle class="lb-dot" cx="${cx}" cy="${cy}" r="6" fill="var(--accent)" />`;
    svg += `<circle class="lb-hit" cx="${cx}" cy="${cy}" r="13" data-model="${row.model}" data-price="${row.price.toFixed(4)}" data-score="${row.score}" />`;
  }
  svg += `</svg>`;

  card.querySelector(".lb-chart-card-inner").innerHTML = svg;
  const tooltip = makeTooltip(card);

  for (const hit of card.querySelectorAll(".lb-hit")) {
    hit.addEventListener("pointerenter", () => {
      const rect = card.getBoundingClientRect();
      const targetRect = hit.getBoundingClientRect();
      showTooltip(
        tooltip,
        targetRect.left - rect.left + targetRect.width / 2,
        targetRect.top - rect.top,
        `<strong>${hit.dataset.score}%</strong><span>${hit.dataset.model} &middot; $${hit.dataset.price}</span>`
      );
    });
    hit.addEventListener("pointerleave", () => hideTooltip(tooltip));
  }
}

function attachTabs() {
  const tabs = document.querySelectorAll(".lb-tab");
  const panels = document.querySelectorAll(".lb-panel");
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      for (const t of tabs) t.classList.remove("active");
      for (const p of panels) p.classList.remove("active");
      tab.classList.add("active");
      document.getElementById(tab.dataset.panel).classList.add("active");
    });
  }
}

renderTable("mcq-table", LEADERBOARD_ROWS);
renderPerfDollarChart();
attachTabs();
