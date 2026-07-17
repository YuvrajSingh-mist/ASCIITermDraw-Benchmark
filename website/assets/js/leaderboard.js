// Leaderboard page. All data below is fabricated placeholder data for
// demonstrating the leaderboard's design -- it does not reflect any real
// model, organization, or benchmark run. Replace with real geval_score
// results (see outputs/<model>/results.csv and metrics.json) once the
// benchmark has enough tracked runs to publish.

const ORG_COLOR = {
  "Nimbus Labs": "var(--lb-series-1)",
  "Continuum AI": "var(--lb-series-2)",
  "Vertex Systems": "var(--lb-series-3)",
  Other: "var(--lb-series-4)",
};

const MCQ_ROWS = [
  { rank: "-", model: "Highest Human Score*", score: 95.4, org: "", reference: true },
  { rank: "-", model: "Human Baseline*", score: 83.7, org: "", reference: true },
  { rank: "1st", model: "Nimbus Ultra", score: 81.9, org: "Nimbus Labs" },
  { rank: "2nd", model: "Solace 3.1 Pro", score: 79.6, org: "Continuum AI" },
  { rank: "3rd", model: "Vertex 5.5 Pro", score: 76.9, org: "Vertex Systems" },
  { rank: "4th", model: "Solace 3.5 Flash", score: 76.7, org: "Continuum AI" },
  { rank: "5th", model: "Solace 3 Pro", score: 76.4, org: "Continuum AI" },
  { rank: "6th", model: "Vertex 5.6 Sol Pro (xhigh)", score: 71.7, org: "Vertex Systems", isNew: true },
  { rank: "7th", model: "Aria 3.7 Max", score: 70.4, org: "Other" },
  { rank: "8th", model: "Flux 4.5", score: 70.0, org: "Other", isNew: true },
  { rank: "9th", model: "Vertex 5.5", score: 69.0, org: "Vertex Systems" },
];

const OPEN_ENDED_ROWS = [
  { rank: "-", model: "Highest Human Score*", score: 91.2, org: "", reference: true },
  { rank: "-", model: "Human Baseline*", score: 78.5, org: "", reference: true },
  { rank: "1st", model: "Solace 3.1 Pro", score: 74.3, org: "Continuum AI" },
  { rank: "2nd", model: "Nimbus Ultra", score: 73.1, org: "Nimbus Labs" },
  { rank: "3rd", model: "Vertex 5.5 Pro", score: 69.8, org: "Vertex Systems" },
  { rank: "4th", model: "Solace 3 Pro", score: 66.5, org: "Continuum AI" },
  { rank: "5th", model: "Vertex 5.6 Sol Pro (xhigh)", score: 64.2, org: "Vertex Systems", isNew: true },
  { rank: "6th", model: "Aria 3.7 Max", score: 61.0, org: "Other" },
  { rank: "7th", model: "Flux 4.5", score: 58.7, org: "Other", isNew: true },
];

const PERF_DOLLAR_POINTS = [
  { model: "Vertex 5.6 Sol Pro", org: "Vertex Systems", price: 6.5, score: 84 },
  { model: "Solace 3.1 Pro", org: "Continuum AI", price: 8.5, score: 86 },
  { model: "Nimbus Ultra", org: "Nimbus Labs", price: 8.0, score: 80 },
  { model: "Nimbus 3", org: "Nimbus Labs", price: 15, score: 76 },
  { model: "Vertex 5.5 Pro", org: "Vertex Systems", price: 130, score: 77 },
  { model: "Solace 3", org: "Continuum AI", price: 8, score: 69 },
  { model: "Vertex 5.5", org: "Vertex Systems", price: 9, score: 70 },
  { model: "Aria 3.7", org: "Other", price: 2, score: 71 },
  { model: "Flux 4.5", org: "Other", price: 2.3, score: 66 },
  { model: "Solace 2.5", org: "Continuum AI", price: 2.2, score: 68 },
  { model: "Nimbus 2 Flash", org: "Nimbus Labs", price: 1.7, score: 59 },
  { model: "Vertex 5.4", org: "Vertex Systems", price: 2.5, score: 52 },
  { model: "Solace 2", org: "Continuum AI", price: 1.5, score: 55 },
  { model: "Flux 4", org: "Other", price: 1.9, score: 48 },
  { model: "Nimbus 2", org: "Nimbus Labs", price: 1, score: 49 },
  { model: "Vertex 5.3", org: "Vertex Systems", price: 1.9, score: 36 },
  { model: "Aria 3.5", org: "Other", price: 45, score: 62 },
  { model: "Solace 1.5", org: "Continuum AI", price: 22, score: 60 },
  { model: "Flux 3", org: "Other", price: 5, score: 52 },
  { model: "Nimbus Lite", org: "Nimbus Labs", price: 0.6, score: 51 },
  { model: "Vertex 5.2", org: "Vertex Systems", price: 5.5, score: 48 },
  { model: "Solace 1", org: "Continuum AI", price: 5.5, score: 41 },
  { model: "Flux 2", org: "Other", price: 5.5, score: 40 },
  { model: "Nimbus Nano", org: "Nimbus Labs", price: 0.18, score: 22 },
  { model: "Solace Mini", org: "Continuum AI", price: 1.6, score: 24 },
];

const TIMELINE_SERIES = [
  {
    org: "Nimbus Labs",
    points: [
      ["Jan", 58], ["Feb", 61], ["Mar", 65], ["Apr", 70], ["May", 74], ["Jun", 78], ["Jul", 82],
    ],
  },
  {
    org: "Continuum AI",
    points: [
      ["Jan", 55], ["Feb", 60], ["Mar", 63], ["Apr", 67], ["May", 72], ["Jun", 79], ["Jul", 86],
    ],
  },
  {
    org: "Vertex Systems",
    points: [
      ["Jan", 52], ["Feb", 57], ["Mar", 62], ["Apr", 66], ["May", 70], ["Jun", 75], ["Jul", 84],
    ],
  },
];

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

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr><th>Rank</th><th>Model</th><th>Score (AVG@5)</th><th>Organization</th></tr>
      </thead>
      <tbody>
        ${rows
          .map((row) => {
            const rowClass = row.reference ? "lb-row-reference" : row.rank === "1st" ? "lb-row-rank1" : "";
            const swatch = row.org
              ? `<span class="lb-legend-swatch" style="display:inline-block;margin-right:0.5rem;background:${ORG_COLOR[row.org] || "transparent"}"></span>`
              : "";
            const badge = row.isNew ? `<span class="lb-new-badge">New</span>` : "";
            return `
              <tr class="${rowClass}">
                <td class="lb-rank">${row.rank}</td>
                <td>${row.model}${badge}</td>
                <td>${row.score.toFixed(1)}%</td>
                <td>${swatch}${row.org}</td>
              </tr>
            `;
          })
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

function showTooltip(tooltip, card, x, y, html) {
  tooltip.innerHTML = html;
  const cardRect = card.getBoundingClientRect();
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
  tooltip.classList.add("active");
}

function hideTooltip(tooltip) {
  tooltip.classList.remove("active");
}

function renderLegend(containerId, orgs) {
  const root = document.getElementById(containerId);
  root.innerHTML = orgs
    .map(
      (org) => `
        <span class="lb-legend-item">
          <span class="lb-legend-swatch" style="background:${ORG_COLOR[org]}"></span>
          ${org}
        </span>
      `
    )
    .join("");
}

function renderPerfDollarChart() {
  const card = document.getElementById("perf-dollar-chart");
  const width = 760;
  const height = 420;
  const margin = { top: 16, right: 16, bottom: 44, left: 44 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const xMin = Math.log10(0.15);
  const xMax = Math.log10(200);
  const yMin = 10;
  const yMax = 90;

  const xScale = (price) => margin.left + ((Math.log10(price) - xMin) / (xMax - xMin)) * plotW;
  const yScale = (score) => margin.top + plotH - ((score - yMin) / (yMax - yMin)) * plotH;

  const xTicks = [0.3, 1, 3, 10, 30, 100];
  const yTicks = [10, 30, 50, 70, 90];

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Score versus dollar cost per benchmark run, by organization">`;

  for (const t of yTicks) {
    const y = yScale(t);
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${t}%</text>`;
  }
  for (const t of xTicks) {
    const x = xScale(t);
    svg += `<text class="lb-tick-label" x="${x}" y="${height - margin.bottom + 16}" text-anchor="middle">$${t}</text>`;
  }
  svg += `<text class="lb-axis-label" x="${margin.left + plotW / 2}" y="${height - 6}" text-anchor="middle">$ per full benchmark run (log) &nbsp;&middot;&nbsp; cheaper &#8592; &#8594; more expensive</text>`;
  svg += `<text class="lb-axis-label" transform="translate(12 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">Score (%)</text>`;

  for (const p of PERF_DOLLAR_POINTS) {
    const cx = xScale(p.price);
    const cy = yScale(p.score);
    svg += `<circle class="lb-dot" cx="${cx}" cy="${cy}" r="6" fill="${ORG_COLOR[p.org]}" data-model="${p.model}" data-org="${p.org}" data-price="${p.price}" data-score="${p.score}" />`;
    svg += `<circle class="lb-hit" cx="${cx}" cy="${cy}" r="13" data-model="${p.model}" data-org="${p.org}" data-price="${p.price}" data-score="${p.score}" />`;
  }
  svg += `</svg>`;

  card.querySelector(".lb-chart-card-inner").innerHTML = svg;
  const tooltip = makeTooltip(card);

  for (const hit of card.querySelectorAll(".lb-hit")) {
    hit.addEventListener("pointerenter", (e) => {
      const rect = card.getBoundingClientRect();
      const targetRect = hit.getBoundingClientRect();
      showTooltip(
        tooltip,
        card,
        targetRect.left - rect.left + targetRect.width / 2,
        targetRect.top - rect.top,
        `<strong>${hit.dataset.score}%</strong><span>${hit.dataset.model} &middot; $${hit.dataset.price}</span>`
      );
    });
    hit.addEventListener("pointerleave", () => hideTooltip(tooltip));
  }

  renderLegend("perf-dollar-legend", ["Nimbus Labs", "Continuum AI", "Vertex Systems", "Other"]);
}

function renderTimelineChart() {
  const card = document.getElementById("timeline-chart");
  const width = 760;
  const height = 360;
  const margin = { top: 16, right: 16, bottom: 36, left: 44 };
  const plotW = width - margin.left - margin.right;
  const plotH = height - margin.top - margin.bottom;

  const months = TIMELINE_SERIES[0].points.map((p) => p[0]);
  const yMin = 40;
  const yMax = 90;

  const xScale = (i) => margin.left + (i / (months.length - 1)) * plotW;
  const yScale = (score) => margin.top + plotH - ((score - yMin) / (yMax - yMin)) * plotH;
  const yTicks = [40, 55, 70, 85];

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Top score by organization over time">`;
  for (const t of yTicks) {
    const y = yScale(t);
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${t}%</text>`;
  }
  months.forEach((m, i) => {
    svg += `<text class="lb-tick-label" x="${xScale(i)}" y="${height - margin.bottom + 18}" text-anchor="middle">${m}</text>`;
  });

  for (const series of TIMELINE_SERIES) {
    const color = ORG_COLOR[series.org];
    const path = series.points
      .map((p, i) => `${i === 0 ? "M" : "L"}${xScale(i)},${yScale(p[1])}`)
      .join(" ");
    svg += `<path class="lb-line" d="${path}" stroke="${color}" />`;
    series.points.forEach((p, i) => {
      svg += `<circle class="lb-dot" cx="${xScale(i)}" cy="${yScale(p[1])}" r="4" fill="${color}" />`;
      svg += `<circle class="lb-hit" cx="${xScale(i)}" cy="${yScale(p[1])}" r="12" data-org="${series.org}" data-month="${p[0]}" data-score="${p[1]}" />`;
    });
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
        card,
        targetRect.left - rect.left + targetRect.width / 2,
        targetRect.top - rect.top,
        `<strong>${hit.dataset.score}%</strong><span>${hit.dataset.org} &middot; ${hit.dataset.month}</span>`
      );
    });
    hit.addEventListener("pointerleave", () => hideTooltip(tooltip));
  }

  renderLegend("timeline-legend", ["Nimbus Labs", "Continuum AI", "Vertex Systems"]);
}

renderTable("mcq-table", MCQ_ROWS);
renderTable("open-ended-table", OPEN_ENDED_ROWS);
renderPerfDollarChart();
renderTimelineChart();
attachTabs();
