// Leaderboard page. Real results, sourced from outputs/<model>/metrics.json
// (via `uv run compute-metrics`) and outputs/<model>/manifest.json for cost
// (both gitignored/private, so the numbers are hand-copied here rather than
// fetched at build time). Update these constants -- and add another entry to
// LEADERBOARD_ROWS -- whenever a new model's results are published.
//
// Generation backends are Together AI and Ollama (see scripts/backends/).
// Per model, 80 tasks, num_judgments=5 (see outputs/<model>/metrics.json):
//   gemma-4-31b-it:      final=0.7380 ci95=[0.6975,0.7786] -> 73.8% +/- 4.1%
//     structural=0.8425+/-0.2468  semantics=0.6336+/-0.1715
//   qwen3.7-plus:        final=0.7015 ci95=[0.6556,0.7474] -> 70.2% +/- 4.6%
//     structural=0.8023+/-0.2644  semantics=0.6008+/-0.2025
//   kimi-k2.6:           final=0.6183 ci95=[0.5581,0.6785] -> 61.8% +/- 6.0%
//     structural=0.7019+/-0.3416  semantics=0.5347+/-0.2551
//   minimax-m3:          final=0.5947 ci95=[0.5320,0.6575] -> 59.5% +/- 6.3%
//     structural=0.6937+/-0.3547  semantics=0.4957+/-0.2578
//   qwen3.5-9b:          final=0.4703 ci95=[0.4062,0.5343] -> 47.0% +/- 6.4%
//     structural=0.5527+/-0.3776  semantics=0.3879+/-0.2507
//   ternary-bonsai-27b:  final=0.4592 ci95=[0.3884,0.5300] -> 45.9% +/- 7.1%
//     structural=0.5192+/-0.3872  semantics=0.3992+/-0.2802
// generation_cost_usd (Together AI, all 80 tasks): gemma-4-31b-it=0.028056,
// qwen3.7-plus=0.03261824, kimi-k2.6=0.300311, minimax-m3=0.099568,
// qwen3.5-9b=0.02788665, ternary-bonsai-27b=0.0 (free-tier Together model).
// Total judging cost (OpenAI gpt-5.4, 5 rounds x 80 tasks, summed cost_usd
// across every outputs/<model>/**/gval/result.json): gemma-4-31b-it=7.8428,
// qwen3.7-plus=7.8761, kimi-k2.6=7.6976, minimax-m3=7.1932,
// qwen3.5-9b=6.6686, ternary-bonsai-27b=6.6043.
//
// Model sizes: dense models (gemma-4-31b-it, qwen3.5-9b, ternary-bonsai-27b)
// are read straight off the model slug. MoE models list total/active params
// as publicly disclosed by their maker: kimi-k2.6 (1T total, 32B active,
// per Moonshot AI's model card) and minimax-m3 (428B total, 23B active,
// per MiniMax's release notes). qwen3.7-plus's parameter count is not
// publicly disclosed by Alibaba -- shown as "undisclosed" rather than guessed.
//
// Second batch (2026-07-22), all run with the text-only default (no --vlm),
// so category 3 sends prompt_text_models.txt (source.ascii inline) instead
// of source.png -- mode: "text". Per model, 80 tasks, num_judgments=5:
//   glm-5.2:             final=0.7060 ci95=[0.6559,0.7562] -> 70.6% +/- 5.0%
//     structural=0.8048+/-0.2740  semantics=0.6072+/-0.2257
//   deepseek-v4-pro:      final=0.6798 ci95=[0.6330,0.7266] -> 68.0% +/- 4.7%
//     structural=0.7719+/-0.2764  semantics=0.5878+/-0.2011
//   kimi-k2.7-code:       final=0.6158 ci95=[0.5459,0.6857] -> 61.6% +/- 7.0%
//     structural=0.6994+/-0.3782  semantics=0.5323+/-0.3078
//   nemotron-3-ultra-550b-a55b: final=0.5738 ci95=[0.5055,0.6422] -> 57.4% +/- 6.8%
//     structural=0.6425+/-0.3737  semantics=0.5052+/-0.2886
//   qwen3.7-max:          final=0.7724 ci95=[0.7321,0.8126] -> 77.2% +/- 4.0%
//     structural=0.8652+/-0.2212  semantics=0.6795+/-0.2002
// generation_cost_usd (Together AI list pricing x actual generation tokens,
// all 80 tasks): glm-5.2=0.1258, deepseek-v4-pro=0.1258,
// kimi-k2.7-code=0.3776, nemotron-3-ultra-550b-a55b=0.2333,
// qwen3.7-max=0.0969.
// Total judging cost (OpenAI gpt-5.4, 5 rounds x 80 tasks, summed cost_usd
// across every output/text/<model>/**/gval/result.json): glm-5.2=7.8621,
// deepseek-v4-pro=7.7517, kimi-k2.7-code=7.1285,
// nemotron-3-ultra-550b-a55b=7.1765, qwen3.7-max=7.8584.
// Params: nemotron-3-ultra-550b-a55b's total/active counts are read straight
// off the model slug (550B total, 55B active), matching the MoE convention
// above. glm-5.2 (743B/39B active), deepseek-v4-pro (1.6T/49B active), and
// kimi-k2.7-code (1T/32B active, same as kimi-k2.6) are each confirmed by
// their maker's own model card. qwen3.7-max is genuinely undisclosed --
// Alibaba has not published a parameter count for either qwen3.7-max or
// qwen3.7-plus as of this writing.
// qwen3.7-max is the highest scorer of any model on the leaderboard so far
// (77.2% final), text-only, no --vlm.
// A fifth model originally tried in this batch (thinkingmachines/Inkling)
// was dropped: it ignores reasoning_effort=none and burns its entire
// --max-tokens budget on hidden reasoning, returning empty diagrams.
// qwen3.7-max was generated as its replacement.
//
// Local Ollama batch (2026-07-22), text-only category-3 prompts, seed 7,
// 80 tasks and 5 GPT-5.4 judge rounds per task. Generation API cost is $0
// for these local runs; hardware and electricity are not estimated.
// Scores and judging costs are copied from outputs/mini2/<model>/metrics.json
// and the corresponding per-task gval/result.json files.

// `mode` marks how each model's category-3 (diagram-editing) requests were
// generated: "vision" = source.png attached as an image (the only path that
// existed when these six were run, and now opt-in via `run-model --vlm`);
// "text" = source.ascii embedded inline in the prompt (the current default,
// no --vlm). Every other category is text-only either way.
const LEADERBOARD_ROWS = [
  {
    model: "gemma-4-31b-it",
    params: "31B",
    org: "Google (via Together AI)",
    mode: "vision",
    genCost: 0.028056,
    judgeCost: 7.8428,
    final: { score: 73.8, margin: 4.1 },
    structural: { score: 84.3, margin: 24.7 },
    semantics: { score: 63.4, margin: 17.2 },
  },
  {
    model: "qwen3.7-plus",
    params: "undisclosed",
    org: "Alibaba (via Together AI)",
    mode: "vision",
    genCost: 0.03261824,
    judgeCost: 7.8761,
    final: { score: 70.2, margin: 4.6 },
    structural: { score: 80.2, margin: 26.4 },
    semantics: { score: 60.1, margin: 20.3 },
  },
  {
    model: "kimi-k2.6",
    params: "1T / 32B active",
    org: "Moonshot AI (via Together AI)",
    mode: "vision",
    genCost: 0.300311,
    judgeCost: 7.6976,
    final: { score: 61.8, margin: 6.0 },
    structural: { score: 70.2, margin: 34.2 },
    semantics: { score: 53.5, margin: 25.5 },
  },
  {
    model: "minimax-m3",
    params: "428B / 23B active",
    org: "MiniMax (via Together AI)",
    mode: "vision",
    genCost: 0.099568,
    judgeCost: 7.1932,
    final: { score: 59.5, margin: 6.3 },
    structural: { score: 69.4, margin: 35.5 },
    semantics: { score: 49.6, margin: 25.8 },
  },
  {
    model: "qwen3.5-9b",
    params: "9B",
    org: "Alibaba (via Together AI)",
    mode: "vision",
    genCost: 0.02788665,
    judgeCost: 6.6686,
    final: { score: 47.0, margin: 6.4 },
    structural: { score: 55.3, margin: 37.8 },
    semantics: { score: 38.8, margin: 25.1 },
  },
  {
    model: "ternary-bonsai-27b",
    params: "27B",
    org: "Prism-ML (via Together AI)",
    mode: "vision",
    genCost: 0.0,
    judgeCost: 6.6043,
    final: { score: 45.9, margin: 7.1 },
    structural: { score: 51.9, margin: 38.7 },
    semantics: { score: 39.9, margin: 28.0 },
  },
  {
    model: "glm-5.2",
    params: "743B / 39B active",
    org: "Z.ai (via Together AI)",
    mode: "text",
    genCost: 0.1258,
    judgeCost: 7.8621,
    final: { score: 70.6, margin: 5.0 },
    structural: { score: 80.5, margin: 27.4 },
    semantics: { score: 60.7, margin: 22.6 },
  },
  {
    model: "deepseek-v4-pro",
    params: "1.6T / 49B active",
    org: "DeepSeek (via Together AI)",
    mode: "text",
    genCost: 0.1258,
    judgeCost: 7.7517,
    final: { score: 68.0, margin: 4.7 },
    structural: { score: 77.2, margin: 27.6 },
    semantics: { score: 58.8, margin: 20.1 },
  },
  {
    model: "kimi-k2.7-code",
    params: "1T / 32B active",
    org: "Moonshot AI (via Together AI)",
    mode: "text",
    genCost: 0.3776,
    judgeCost: 7.1285,
    final: { score: 61.6, margin: 7.0 },
    structural: { score: 69.9, margin: 37.8 },
    semantics: { score: 53.2, margin: 30.8 },
  },
  {
    model: "nemotron-3-ultra-550b-a55b",
    params: "550B / 55B active",
    org: "NVIDIA (via Together AI)",
    mode: "text",
    genCost: 0.2333,
    judgeCost: 7.1765,
    final: { score: 57.4, margin: 6.8 },
    structural: { score: 64.3, margin: 37.4 },
    semantics: { score: 50.5, margin: 28.9 },
  },
  {
    model: "qwen3.7-max",
    params: "undisclosed",
    org: "Alibaba (via Together AI)",
    mode: "text",
    genCost: 0.0969,
    judgeCost: 7.8584,
    final: { score: 77.2, margin: 4.0 },
    structural: { score: 86.5, margin: 22.1 },
    semantics: { score: 68.0, margin: 20.0 },
  },
  {
    model: "falcon-h1-1.5b-instruct-gguf-q4_k_m",
    params: "1.5B",
    org: "TII (local Ollama)",
    mode: "text",
    genCost: 0.0,
    judgeCost: 7.4253,
    final: { score: 31.2, margin: 4.2 },
    structural: { score: 43.6, margin: 32.3 },
    semantics: { score: 18.9, margin: 13.2 },
  },
  {
    model: "lfm2.5-1.2b-instruct-q4_k_m",
    params: "1.2B",
    org: "Liquid AI (local Ollama)",
    mode: "text",
    genCost: 0.0,
    judgeCost: 6.4529,
    final: { score: 30.5, margin: 4.4 },
    structural: { score: 45.2, margin: 31.6 },
    semantics: { score: 15.9, margin: 15.3 },
  },
  {
    model: "gemma3-1b",
    params: "1B",
    org: "Google (local Ollama)",
    mode: "text",
    genCost: 0.0,
    judgeCost: 6.5984,
    final: { score: 23.0, margin: 4.1 },
    structural: { score: 23.0, margin: 29.1 },
    semantics: { score: 23.0, margin: 12.4 },
  },
  {
    model: "granite-4.0-h-1b-gguf-q4_k_m",
    params: "1B",
    org: "IBM (local Ollama)",
    mode: "text",
    genCost: 0.0,
    judgeCost: 5.8179,
    final: { score: 22.5, margin: 5.3 },
    structural: { score: 24.0, margin: 33.8 },
    semantics: { score: 21.1, margin: 18.5 },
  },
  {
    model: "qwen3-1.7b",
    params: "1.7B",
    org: "Alibaba (local Ollama)",
    mode: "text",
    genCost: 0.0,
    judgeCost: 6.1838,
    final: { score: 19.8, margin: 5.4 },
    structural: { score: 23.7, margin: 33.1 },
    semantics: { score: 16.0, margin: 18.9 },
  },
];

const MODE_FILTERS = {
  all: { label: "All" },
  vision: { label: "Vision" },
  text: { label: "Text-only" },
};

let currentModeFilter = "all";

function ordinal(n) {
  const rem100 = n % 100;
  if (rem100 >= 11 && rem100 <= 13) return `${n}th`;
  switch (n % 10) {
    case 1:
      return `${n}st`;
    case 2:
      return `${n}nd`;
    case 3:
      return `${n}rd`;
    default:
      return `${n}th`;
  }
}

// Dense models use their total parameter count; MoE models use the disclosed
// active count. Undisclosed sizes sort last. Performance rank is calculated
// separately, so changing the display order does not redefine leaderboard rank.
function activeParamsBillions(params) {
  const activeMatch = params.match(/\/\s*([\d.]+)([BT])\s+active/i);
  const denseMatch = params.match(/^([\d.]+)([BT])/i);
  const match = activeMatch || denseMatch;
  if (!match) return Number.POSITIVE_INFINITY;
  return Number(match[1]) * (match[2].toUpperCase() === "T" ? 1000 : 1);
}

function rankedRows(rows) {
  const performanceRanks = new Map(
    [...rows]
      .sort((a, b) => b.final.score - a.final.score)
      .map((row, index) => [row.model, ordinal(index + 1)])
  );

  return [...rows]
    .sort((a, b) =>
      activeParamsBillions(a.params) - activeParamsBillions(b.params) ||
      a.model.localeCompare(b.model)
    )
    .map((row) => ({ ...row, rank: performanceRanks.get(row.model) }));
}

function getFilteredRows() {
  if (currentModeFilter === "all") return LEADERBOARD_ROWS;
  return LEADERBOARD_ROWS.filter((row) => row.mode === currentModeFilter);
}

function renderModeFilter() {
  const root = document.getElementById("lb-mode-filter");
  if (!root) return;
  root.innerHTML = Object.entries(MODE_FILTERS)
    .map(([key, meta]) => {
      const count = key === "all" ? LEADERBOARD_ROWS.length : LEADERBOARD_ROWS.filter((r) => r.mode === key).length;
      return `
        <button class="lb-mode-btn${key === currentModeFilter ? " active" : ""}" data-mode="${key}" role="tab" aria-selected="${key === currentModeFilter}">
          ${meta.label}
          <span class="lb-mode-count">${count}</span>
        </button>
      `;
    })
    .join("");
  for (const btn of root.querySelectorAll(".lb-mode-btn")) {
    btn.addEventListener("click", () => {
      if (btn.dataset.mode === currentModeFilter) return;
      currentModeFilter = btn.dataset.mode;
      renderLeaderboard();
    });
  }
}

const METRICS = {
  final: { label: "Final", statLabel: "mean, 95% CI" },
  structural: { label: "Structural", statLabel: "mean &plusmn; stdev" },
  semantics: { label: "Semantics", statLabel: "mean &plusmn; stdev" },
};

function renderTable(containerId, rows) {
  const root = document.getElementById(containerId);
  if (rows.length === 0) {
    root.innerHTML = `<p class="lb-empty">No models benchmarked yet for this generation mode.</p>`;
    return;
  }
  root.innerHTML = `
    <table class="lb-table">
      <thead>
        <tr>
          <th>Score rank</th>
          <th>Model</th>
          <th>Active params &#8593;</th>
          <th>Score (95% CI, 80 tasks)</th>
          <th>Structural</th>
          <th>Semantic</th>
          <th>Gen Cost</th>
          <th>Judging Cost</th>
          <th>Organization</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr class="${row.rank === "1st" ? "lb-row-rank1" : ""}">
                <td class="lb-rank">${row.rank}</td>
                <td>${row.model}</td>
                <td class="lb-params">${row.params}</td>
                <td>${row.final.score.toFixed(1)}% &plusmn; ${row.final.margin.toFixed(1)}%</td>
                <td class="lb-score">${row.structural.score.toFixed(1)}%</td>
                <td class="lb-score">${row.semantics.score.toFixed(1)}%</td>
                <td>$${row.genCost.toFixed(4)}</td>
                <td>$${row.judgeCost.toFixed(2)}</td>
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
let pinnedChartTooltip = null;

document.addEventListener("click", (event) => {
  if (!pinnedChartTooltip || event.target.closest(".lb-hit")) return;
  hideTooltip(pinnedChartTooltip.tooltip);
  pinnedChartTooltip = null;
});

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
  const margin = { top: 16, right: 24, bottom: 44, left: 68 };
  const plotH = height - margin.top - margin.bottom;
  const paidPlotStart = 250;
  const paidPlotWidth = width - margin.right - paidPlotStart;
  const localBandStart = margin.left + 18;
  const localBandEnd = paidPlotStart - 24;

  const xMin = Math.log10(0.01);
  const xMax = Math.log10(1);
  const yMin = 0;
  const yMax = 100;
  const visibleRows = getFilteredRows();

  const xScalePrice = (price) =>
    paidPlotStart +
    ((Math.log10(Math.max(price, 10 ** xMin)) - xMin) / (xMax - xMin)) * paidPlotWidth;
  const yScale = (score) => margin.top + plotH - ((score - yMin) / (yMax - yMin)) * plotH;

  // Zero-API-cost runs need a categorical band: log10(0) is undefined, and
  // pinning every free/local model to $0.01 makes the points indistinguishable.
  const localRows = visibleRows
    .filter((row) => row.genCost <= 0)
    .sort((a, b) => a.model.localeCompare(b.model));
  const localXByModel = new Map(
    localRows.map((row, index) => {
      const ratio = localRows.length === 1 ? 0.5 : index / (localRows.length - 1);
      return [row.model, localBandStart + ratio * (localBandEnd - localBandStart)];
    })
  );

  // Paid points retain their true log-scaled x position. If two nearby points
  // would overlap, move them sideways by the smallest possible amount.
  const pointLayouts = [];
  const offsetCandidates = [0, -28, 28, -56, 56, -84, 84, -112, 112];
  for (const row of [...visibleRows].sort((a, b) => a.genCost - b.genCost || a.model.localeCompare(b.model))) {
    const point = row[currentChartMetric];
    const cy = yScale(point.score);
    const isLocal = row.genCost <= 0;
    const baseX = isLocal ? localXByModel.get(row.model) : xScalePrice(row.genCost);
    let cx = baseX;

    if (!isLocal) {
      for (const offset of offsetCandidates) {
        const candidateX = Math.max(paidPlotStart, Math.min(width - margin.right, baseX + offset));
        const overlaps = pointLayouts.some(
          (placed) => Math.hypot(candidateX - placed.cx, cy - placed.cy) < 28
        );
        if (!overlaps) {
          cx = candidateX;
          break;
        }
      }
    }

    pointLayouts.push({ row, point, cx, cy });
  }

  const xTicks = [0.01, 0.03, 0.1, 0.3, 1];
  const yTicks = [0, 25, 50, 75, 100];
  const metricMeta = METRICS[currentChartMetric];
  const localBandCenter = (localBandStart + localBandEnd) / 2;

  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${metricMeta.label} score (${metricMeta.statLabel.replace(/&plusmn;/g, "+/-")}) versus generation API cost per full benchmark run">`;

  for (const t of yTicks) {
    const y = yScale(t);
    svg += `<line class="lb-grid-line" x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" />`;
    svg += `<text class="lb-tick-label" x="${margin.left - 8}" y="${y + 3}" text-anchor="end">${t}%</text>`;
  }
  if (localRows.length > 0) {
    svg += `<text class="lb-tick-label" x="${localBandCenter}" y="${height - margin.bottom + 16}" text-anchor="middle">$0 API</text>`;
    svg += `<line class="lb-cost-band-divider" x1="${paidPlotStart - 12}" y1="${margin.top}" x2="${paidPlotStart - 12}" y2="${margin.top + plotH}" />`;
  }
  for (const t of xTicks) {
    const x = xScalePrice(t);
    svg += `<text class="lb-tick-label" x="${x}" y="${height - margin.bottom + 16}" text-anchor="middle">$${t}</text>`;
  }
  svg += `<text class="lb-axis-label" x="${margin.left + (width - margin.right - margin.left) / 2}" y="${height - 6}" text-anchor="middle">Generation API cost per full run &nbsp;&middot;&nbsp; paid models use a log scale</text>`;
  svg += `<text class="lb-axis-label" transform="translate(14 ${margin.top + plotH / 2}) rotate(-90)" text-anchor="middle">${metricMeta.label} score (%)</text>`;

  for (const { row, point, cx, cy } of pointLayouts) {
    const yTop = yScale(Math.min(100, point.score + point.margin));
    const yBottom = yScale(Math.max(0, point.score - point.margin));
    const capHalfWidth = 7;
    const priceLabel = row.genCost <= 0 ? "$0 API" : "$" + row.genCost.toFixed(4);
    // Whisker: final uses a 95% CI; structural/semantics use one population
    // stdev. The x-offset only prevents visual collisions and does not alter cost.
    svg += `<line class="lb-whisker" x1="${cx}" y1="${yTop}" x2="${cx}" y2="${yBottom}" />`;
    svg += `<line class="lb-whisker-cap" x1="${cx - capHalfWidth}" y1="${yTop}" x2="${cx + capHalfWidth}" y2="${yTop}" />`;
    svg += `<line class="lb-whisker-cap" x1="${cx - capHalfWidth}" y1="${yBottom}" x2="${cx + capHalfWidth}" y2="${yBottom}" />`;
    svg += `<circle class="lb-dot" cx="${cx}" cy="${cy}" r="6" fill="var(--accent)" />`;
    svg += `<circle class="lb-hit" cx="${cx}" cy="${cy}" r="13" tabindex="0" role="button" aria-label="${row.model}: ${point.score}% plus or minus ${point.margin}%, ${priceLabel}" data-model="${row.model}" data-price-label="${priceLabel}" data-score="${point.score}" data-score-margin="${point.margin}" data-stat-label="${metricMeta.statLabel}" />`;
  }
  svg += `</svg>`;

  card.querySelector(".lb-chart-card-inner").innerHTML = svg;
  renderMetricToggle(card);
  if (pinnedChartTooltip) {
    hideTooltip(pinnedChartTooltip.tooltip);
    pinnedChartTooltip = null;
  }
  const tooltip = makeTooltip(card);

  function displayHitTooltip(hit) {
    const rect = card.getBoundingClientRect();
    const targetRect = hit.getBoundingClientRect();
    showTooltip(
      tooltip,
      targetRect.left - rect.left + targetRect.width / 2,
      targetRect.top - rect.top,
      `<strong>${hit.dataset.score}% &plusmn; ${hit.dataset.scoreMargin}%</strong><span>${hit.dataset.model} &middot; ${hit.dataset.priceLabel}</span>`
    );
  }

  for (const hit of card.querySelectorAll(".lb-hit")) {
    hit.addEventListener("pointerenter", () => {
      if (!pinnedChartTooltip) displayHitTooltip(hit);
    });
    hit.addEventListener("pointerleave", () => {
      if (!pinnedChartTooltip) hideTooltip(tooltip);
    });
    hit.addEventListener("click", (event) => {
      event.stopPropagation();
      displayHitTooltip(hit);
      pinnedChartTooltip = { hit, tooltip };
    });
    hit.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        displayHitTooltip(hit);
        pinnedChartTooltip = { hit, tooltip };
      }
    });
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

function renderLeaderboard() {
  renderModeFilter();
  renderTable("mcq-table", rankedRows(getFilteredRows()));
  renderPerfDollarChart();
}

renderLeaderboard();
attachTabs();
