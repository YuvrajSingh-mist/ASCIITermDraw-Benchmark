import { readdirSync, writeFileSync, existsSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const TASKS_DIR = join(ROOT, "tasks");
const OUT = join(ROOT, "website", "assets", "data", "site_data.json");

const HF_DATASET = "YuvrajSingh9886/asciitermdraw-bench-public";
const HF_RESOLVE_BASE = `https://huggingface.co/datasets/${HF_DATASET}/resolve/main`;

// The 12 public example tasks (one per category/difficulty), as laid out in
// the Hugging Face dataset (https://huggingface.co/datasets/YuvrajSingh9886/asciitermdraw-bench-public).
// Prompt text and reference images are fetched directly from HF at build
// time rather than from a local copy -- there is no public_dataset/ in this
// repository.
const PUBLIC_EXAMPLE_TASKS = [
  { dir: "box-layout-basics", difficulty: "easy", taskId: "0.1" },
  { dir: "box-layout-basics", difficulty: "medium", taskId: "0.2" },
  { dir: "box-layout-basics", difficulty: "hard", taskId: "0.3" },
  { dir: "diagram-editing", difficulty: "easy", taskId: "0.4" },
  { dir: "diagram-editing", difficulty: "medium", taskId: "0.5" },
  { dir: "diagram-editing", difficulty: "hard", taskId: "0.6" },
  { dir: "network-topology-diagrams", difficulty: "easy", taskId: "0.7" },
  { dir: "network-topology-diagrams", difficulty: "medium", taskId: "0.8" },
  { dir: "network-topology-diagrams", difficulty: "hard", taskId: "0.9" },
  { dir: "software-architecture-diagrams", difficulty: "easy", taskId: "0.10" },
  { dir: "software-architecture-diagrams", difficulty: "medium", taskId: "0.11" },
  { dir: "software-architecture-diagrams", difficulty: "hard", taskId: "0.12" },
];

// Boilerplate rubric bullets repeated verbatim across every task's prompt.txt.
// They're required in the real prompt (it's what's sent to the model), but
// showing them on every public-example card would be repetitive, so the
// website's trimmed prompt display drops these specific lines only.
const PROMPT_DISPLAY_STRIP_LINES = new Set([
  "When arrows are required, make them centered and aligned cleanly to their source and target.",
  "If an arrow has a label, place the label a little above the arrow rather than inside the arrow line.",
  "For any label or text inside a node, box, or icon, center it within that component whenever possible.",
  "Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate.",
  "If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points.",
  "Return only the final ASCII diagram in plain text.",
  "Do not include markdown fences, explanations, or any extra text.",
]);

function trimPromptForDisplay(promptText) {
  return promptText
    .split(/\r?\n/)
    .filter((line) => !PROMPT_DISPLAY_STRIP_LINES.has(line.replace(/^-\s*/, "").trim()))
    .join("\n")
    .trim();
}

const CATEGORY_META = {
  "1": {
    dir: "box-layout-basics",
    name: "Box Layout Basics",
    description:
      "Single boxes, rows, columns, arrows, lanes, and spacing-sensitive ASCII layout tasks.",
  },
  "2": {
    dir: "network-topology-diagrams",
    name: "Network Topology Diagrams",
    description:
      "Distributed systems, clusters, buses, data flows, and topology-heavy connection diagrams.",
  },
  "3": {
    dir: "diagram-editing",
    name: "Diagram Editing",
    description:
      "Image-to-text edit tasks where a model must transform an existing ASCII diagram correctly.",
  },
  "4": {
    dir: "software-architecture-diagrams",
    name: "Software Architecture Diagrams",
    description:
      "Real-world system architectures — API gateways, event pipelines, feeds, rate limiters, and storage layers — as they'd actually be sketched on a whiteboard.",
  },
};

// tasks/ is private and not shipped to CI (see .gitignore), so a public build
// has no way to count real tasks per category. These are the true, static
// counts from the actual benchmark (verified against the private tasks/
// tree) -- used only as a fallback when tasks/ isn't present, so the public
// site still reports real numbers instead of zeros. Per-task content (which
// *is* private) is never substituted -- only these aggregate counts.
const STATIC_TASK_COUNTS = {
  "box-layout-basics": { easy: 10, medium: 5, hard: 5 },
  "network-topology-diagrams": { easy: 10, medium: 5, hard: 5 },
  "diagram-editing": { easy: 10, medium: 5, hard: 5 },
  "software-architecture-diagrams": { easy: 10, medium: 5, hard: 5 },
};

function parseTaskId(taskId) {
  const [category, index] = taskId.split(".").map(Number);
  return { category, index };
}

function taskSort(a, b) {
  const left = parseTaskId(a);
  const right = parseTaskId(b);
  if (left.category !== right.category) {
    return left.category - right.category;
  }
  return left.index - right.index;
}

function collectTaskDirs(dir) {
  if (!existsSync(dir)) {
    return [];
  }
  const entries = readdirSync(dir, { withFileTypes: true });
  const taskDirs = [];
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (!entry.isDirectory()) {
      continue;
    }
    if (/^\d+\.\d+$/.test(entry.name)) {
      taskDirs.push(fullPath);
      continue;
    }
    taskDirs.push(...collectTaskDirs(fullPath));
  }
  return taskDirs;
}

async function fetchText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} for ${url}`);
  }
  return response.text();
}

async function collectPublicExamples() {
  const nameByDir = Object.fromEntries(
    Object.values(CATEGORY_META).map((meta) => [meta.dir, meta.name])
  );
  const examples = [];
  for (const { dir, difficulty, taskId } of PUBLIC_EXAMPLE_TASKS) {
    const base = `${HF_RESOLVE_BASE}/${dir}/${difficulty}/${taskId}`;
    try {
      const promptText = await fetchText(`${base}/prompt.txt`);
      const hasSource = dir === "diagram-editing";
      examples.push({
        category_slug: dir,
        category_name: nameByDir[dir],
        difficulty,
        task_id: taskId,
        prompt: trimPromptForDisplay(promptText),
        img: `${base}/reference.png`,
        has_source: hasSource,
        source_img: hasSource ? `${base}/source.png` : null,
      });
    } catch (err) {
      // A CI runner without network egress (or a transient HF outage)
      // shouldn't fail the whole site build -- just skip that example and
      // note it, since these are public examples, not private task content.
      console.warn(`Skipping public example ${dir}/${difficulty}/${taskId}: ${err.message}`);
    }
  }
  return examples;
}

async function build() {
  const categories = [];
  let totalTasks = 0;
  let totalEditTasks = 0;

  for (const [categoryId, meta] of Object.entries(CATEGORY_META)) {
    const categoryDir = join(TASKS_DIR, meta.dir);
    const tasks = collectTaskDirs(categoryDir)
      .sort((a, b) => taskSort(a.split("/").at(-1), b.split("/").at(-1)))
      .filter((taskDir) => existsSync(taskDir))
      .map((taskDir) => {
        const hasSource = existsSync(join(taskDir, "source.ascii"));
        if (hasSource) {
          totalEditTasks += 1;
        }
        // Intentionally minimal: only what's needed for aggregate counts on
        // the public site (difficulty breakdowns, edit-task counts). Prompt
        // text and ASCII previews are private task content and are not
        // published — see the Hugging Face dataset for public examples.
        return {
          task_id: taskDir.split("/").at(-1),
          path: relative(ROOT, taskDir),
          has_source: hasSource,
        };
      });

    let difficulty = { easy: 0, medium: 0, hard: 0 };
    for (const task of tasks) {
      if (task.path.includes("/easy/")) difficulty.easy += 1;
      if (task.path.includes("/medium/")) difficulty.medium += 1;
      if (task.path.includes("/hard/")) difficulty.hard += 1;
    }
    let count = tasks.length;
    let usedFallback = false;
    if (count === 0 && STATIC_TASK_COUNTS[meta.dir]) {
      difficulty = { ...STATIC_TASK_COUNTS[meta.dir] };
      count = difficulty.easy + difficulty.medium + difficulty.hard;
      usedFallback = true;
    }

    totalTasks += count;
    if (usedFallback && meta.dir === "diagram-editing") {
      // Every diagram-editing task is image-conditioned (has a source.ascii);
      // real has_source detection is unavailable without the private tree.
      totalEditTasks += count;
    }
    categories.push({
      id: categoryId,
      slug: meta.dir,
      name: meta.name,
      description: meta.description,
      count,
      difficulty,
      tasks,
    });
  }

  const payload = {
    title: "ASCIITermDraw-Bench",
    summary: "Benchmark for ASCII diagram generation and editing.",
    stats: {
      task_count: totalTasks,
      category_count: categories.length,
      edit_task_count: totalEditTasks,
      rendered_reference_count: totalTasks,
    },
    categories,
    public_examples: await collectPublicExamples(),
  };

  writeFileSync(OUT, `${JSON.stringify(payload, null, 2)}\n`);
}

await build();
