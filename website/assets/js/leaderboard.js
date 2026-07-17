// Leaderboard page. Real results, sourced from outputs/<model>/metrics.json
// (via `uv run compute-metrics`) and outputs/<model>/manifest.json for cost
// (both gitignored/private, so the numbers are hand-copied here rather than
// fetched at build time). Update these constants -- and add another entry to
// LEADERBOARD_ROWS -- whenever a new model's results are published.
//
// Per model, 80 tasks, num_judgments=5 (see outputs/<model>/metrics.json):
//   final_score.mean/ci95 (95% CI, 80 tasks as the independent sampling unit,
//     not the 400 judge rounds -- see scripts/judge/compute_metrics.py):
//     qwen3p7-plus:  0.6713 +/- 0.0505 -> 67.1% +/- 5.1%
//     minimax-m3:    0.6693 +/- 0.0499 -> 66.9% +/- 5.0%
//     kimi-k2p6:     0.5880 +/- 0.0583 -> 58.8% +/- 5.8%
//   structural.mean/stdev, semantics.mean/stdev (population stdev over every
//     judge round across all tasks -- descriptive spread, not a CI):
//     qwen3p7-plus:  structural=0.7679+/-0.2842  semantics=0.5746+/-0.2284
//     minimax-m3:    structural=0.7767+/-0.2836  semantics=0.5620+/-0.2221
//     kimi-k2p6:     structural=0.6794+/-0.3185  semantics=0.4967+/-0.2602
// generation_cost_usd (Fireworks, all 80 tasks): qwen3p7-plus=0.058589,
// minimax-m3=0.055967, kimi-k2p6=0.258444.

const LEADERBOARD_ROWS = [
  {
    rank: "1st",
    model: "qwen3p7-plus",
    org: "Alibaba (via Fireworks)",
    price: 0.058589,
    final: { score: 67.1, margin: 5.1 },
    structural: { score: 76.8, margin: 28.4 },
    semantics: { score: 57.5, margin: 22.8 },
  },
  {
    rank: "2nd",
    model: "minimax-m3",
    org: "MiniMax (via Fireworks)",
    price: 0.055967,
    final: { score: 66.9, margin: 5.0 },
    structural: { score: 77.7, margin: 28.4 },
    semantics: { score: 56.2, margin: 22.2 },
  },
  {
    rank: "3rd",
    model: "kimi-k2p6",
    org: "Moonshot AI (via Fireworks)",
    price: 0.258444,
    final: { score: 58.8, margin: 5.8 },
    structural: { score: 67.9, margin: 31.9 },
    semantics: { score: 49.7, margin: 26.0 },
  },
];

const METRICS = {
  final: { label: "Final", statLabel: "mean, 95% CI" },
  structural: { label: "Structural", statLabel: "mean &plusmn; stdev" },
  semantics: { label: "Semantics", statLabel: "mean &plusmn; stdev" },
};

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr><th>Rank</th><th>Model</th><th>Score (95% CI, 80 tasks)</th><th>Organization</th></tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr class="${row.rank === "1st" ? "lb-row-rank1" : ""}">
                <td class="lb-rank">${row.rank}</td>
                <td>${row.model}</td>
                <td>${row.final.score.toFixed(1)}% &plusmn; ${row.final.margin.toFixed(1)}%</td>
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
  const existing = card.querySelector(".lb-tooltip");
  if (existing) existing.remove();
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

let currentChartMetric = "final";

function renderMetricToggle(card) {
  const root = card.querySelector(".lb-metric-toggle");
  if (!root) return;
  root.innerHTML = Object.entries(METRICS)
    .map(
      ([key, meta]) => `
        <button class="lb-metric-btn${key === currentChartMetric ? " active" : ""}" data-metric="${key}">${meta.label}</button>
      `
    )
    .join("");
  for (const btn of root.querySelectorAll(".lb-metric-btn")) {
    btn.addEventListener("click", () => {
      currentChartMetric = btn.dataset.metric;
      renderPerfDollarChart();
    });
  }
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

  const metricMeta = METRICS[currentChartMetric];

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${metricMeta.label} score (${metricMeta.statLabel.replace(/&plusmn;/g, "+/-")}) versus Fireworks generation cost per full benchmark run">`;

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
  svg += `<text class="lb-axis-label" transform="translate(12 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">${metricMeta.label} score (%)</text>`;

  for (const row of LEADERBOARD_ROWS) {
    const point = row[currentChartMetric];
    const cx = xScale(row.price);
    const cy = yScale(point.score);
    const yTop = yScale(Math.min(100, point.score + point.margin));
    const yBottom = yScale(Math.max(0, point.score - point.margin));
    const capHalfWidth = 7;
    // Whisker: for "final" this is a 95% CI on the mean (1.96 *
    // sample_stdev / sqrt(80) over the 80 tasks); for structural/semantics
    // it's +/-1 population stdev (descriptive spread, not an inferential
    // CI). Either way, not a box plot -- no quartiles/median available.
    svg += `<line class="lb-whisker" x1="${cx}" y1="${yTop}" x2="${cx}" y2="${yBottom}" />`;
    svg += `<line class="lb-whisker-cap" x1="${cx - capHalfWidth}" y1="${yTop}" x2="${cx + capHalfWidth}" y2="${yTop}" />`;
    svg += `<line class="lb-whisker-cap" x1="${cx - capHalfWidth}" y1="${yBottom}" x2="${cx + capHalfWidth}" y2="${yBottom}" />`;
    svg += `<circle class="lb-dot" cx="${cx}" cy="${cy}" r="6" fill="var(--accent)" />`;
    svg += `<circle class="lb-hit" cx="${cx}" cy="${cy}" r="13" data-model="${row.model}" data-price="${row.price.toFixed(4)}" data-score="${point.score}" data-score-margin="${point.margin}" data-stat-label="${metricMeta.statLabel}" />`;
  }
  svg += `</svg>`;

  card.querySelector(".lb-chart-card-inner").innerHTML = svg;
  renderMetricToggle(card);
  const tooltip = makeTooltip(card);

  for (const hit of card.querySelectorAll(".lb-hit")) {
    hit.addEventListener("pointerenter", () => {
      const rect = card.getBoundingClientRect();
      const targetRect = hit.getBoundingClientRect();
      showTooltip(
        tooltip,
        targetRect.left - rect.left + targetRect.width / 2,
        targetRect.top - rect.top,
        `<strong>${hit.dataset.score}% &plusmn; ${hit.dataset.scoreMargin}%</strong><span>${hit.dataset.model} &middot; $${hit.dataset.price}</span>`
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
