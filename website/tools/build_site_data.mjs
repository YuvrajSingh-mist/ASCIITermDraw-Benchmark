import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
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
      "Canonical architecture sketches such as gateways, pipelines, feeds, rate limiters, and storage systems.",
  },
};

function readText(path) {
  return readFileSync(path, "utf8");
}

function titleFromJudge(taskDir) {
  const firstLine = readText(join(taskDir, "vlm_judge_prompt.txt")).split(/\r?\n/, 1)[0].trim();
  if (firstLine.startsWith("TASK:")) {
    return firstLine.replace("TASK:", "").split("(Task", 1)[0].trim();
  }
  return firstLine;
}

function previewFromReference(taskDir) {
  return readText(join(taskDir, "reference.ascii"))
    .split(/\r?\n/)
    .slice(0, 6)
    .join("\n");
}

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
        return {
          task_id: taskDir.split("/").at(-1),
          title: titleFromJudge(taskDir),
          prompt: readText(join(taskDir, "prompt.txt")).trim(),
          path: relative(ROOT, taskDir),
          has_source: hasSource,
          preview: previewFromReference(taskDir),
        };
      });

    totalTasks += tasks.length;
    categories.push({
      id: categoryId,
      slug: meta.dir,
      name: meta.name,
      description: meta.description,
      count: tasks.length,
      tasks,
    });
  }

  const payload = {
    title: "TermDraw-Bench",
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
