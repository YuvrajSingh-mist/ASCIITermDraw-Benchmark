import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const TASKS_DIR = join(ROOT, "tasks");
const PUBLIC_DIR = join(ROOT, "public_dataset");
const PUBLIC_IMG_OUT_DIR = join(ROOT, "website", "assets", "img", "public-dataset");
const OUT = join(ROOT, "website", "assets", "data", "site_data.json");

// Boilerplate rubric bullets repeated verbatim across every task's prompt.txt.
// They're required in the real prompt (it's what's sent to the model), but
// showing them on every public-example card would be repetitive, so the
// website's trimmed prompt display drops these specific lines only.
const PROMPT_DISPLAY_STRIP_LINES = new Set([
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
      "Canonical architecture sketches such as gateways, pipelines, feeds, rate limiters, and storage systems.",
  },
};

function readText(path) {
  return readFileSync(path, "utf8");
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

const DIFFICULTY_ORDER = { easy: 0, medium: 1, hard: 2 };

function collectPublicExamples() {
  if (!existsSync(PUBLIC_DIR)) {
    return [];
  }
  mkdirSync(PUBLIC_IMG_OUT_DIR, { recursive: true });

  const examples = [];
  for (const [, meta] of Object.entries(CATEGORY_META)) {
    const categoryDir = join(PUBLIC_DIR, meta.dir);
    if (!existsSync(categoryDir)) {
      continue;
    }
    for (const difficulty of ["easy", "medium", "hard"]) {
      const difficultyDir = join(categoryDir, difficulty);
      if (!existsSync(difficultyDir)) {
        continue;
      }
      // The leaf directory is a real task id (e.g. "0.1"), matching the same
      // <category>/<difficulty>/<task_id> layout run-model/judge-geval expect.
      const taskIdDir = readdirSync(difficultyDir, { withFileTypes: true }).find((entry) =>
        entry.isDirectory() && /^\d+\.\d+$/.test(entry.name)
      );
      if (!taskIdDir) {
        continue;
      }
      const taskDir = join(difficultyDir, taskIdDir.name);
      const referencePng = join(taskDir, "reference.png");
      if (!existsSync(referencePng)) {
        continue;
      }
      const imgFilename = `${meta.dir}-${difficulty}.png`;
      copyFileSync(referencePng, join(PUBLIC_IMG_OUT_DIR, imgFilename));
      examples.push({
        category_slug: meta.dir,
        category_name: meta.name,
        difficulty,
        task_id: taskIdDir.name,
        prompt: trimPromptForDisplay(readText(join(taskDir, "prompt.txt"))),
        img: `img/public-dataset/${imgFilename}`,
        has_source: existsSync(join(taskDir, "source.ascii")),
      });
    }
  }
  examples.sort((a, b) => {
    if (a.category_slug !== b.category_slug) {
      return a.category_slug.localeCompare(b.category_slug);
    }
    return DIFFICULTY_ORDER[a.difficulty] - DIFFICULTY_ORDER[b.difficulty];
  });
  return examples;
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
        // published — see public_examples for the safe, public equivalent.
        return {
          task_id: taskDir.split("/").at(-1),
          path: relative(ROOT, taskDir),
          has_source: hasSource,
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
    title: "ASCIITermDraw-Bench",
    summary: "Benchmark for ASCII diagram generation and editing.",
    stats: {
      task_count: totalTasks,
      category_count: categories.length,
      edit_task_count: totalEditTasks,
      rendered_reference_count: totalTasks,
    },
    categories,
    public_examples: collectPublicExamples(),
  };

  writeFileSync(OUT, `${JSON.stringify(payload, null, 2)}\n`);
}

build();
