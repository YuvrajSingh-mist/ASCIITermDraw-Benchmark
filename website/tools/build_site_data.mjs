import { readdirSync, writeFileSync, existsSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const TASKS_DIR = join(ROOT, "tasks");
const OUT = join(ROOT, "website", "assets", "data", "site_data.json");

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

function build() {
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
  };

  writeFileSync(OUT, `${JSON.stringify(payload, null, 2)}\n`);
}

build();
