// Renders a single .ascii file to a diagram-only PNG using headless Playwright/Chromium.
// Invoked as: node scripts/rendered/render_ascii.mjs <input.ascii> <output.png>
// Called from Python via scripts/rendered/render.py (subprocess) and scripts/judge/geval_support.py (candidate PNG rendering).
import { readFile } from "node:fs/promises";
import { chromium } from "playwright";

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  console.error("Usage: node scripts/rendered/render_ascii.mjs <input.ascii> <output.png>");
  process.exit(1);
}

const text = await readFile(input, "utf8");

const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
});
const page = await browser.newPage({ deviceScaleFactor: 2 });

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <style>
      html, body {
        margin: 0;
        padding: 0;
        background: #ffffff;
      }
      body {
        display: inline-block;
        padding: 24px 28px;
        font-family: Menlo, Monaco, "Cascadia Mono", "SF Mono", Consolas, monospace;
      }
      pre {
        margin: 0;
        color: #111827;
        background: #ffffff;
        font-size: 22px;
        line-height: 1.2;
        letter-spacing: 0;
        white-space: pre;
      }
    </style>
  </head>
  <body>
    <pre id="diagram"></pre>
    <script>
      document.getElementById("diagram").textContent = ${JSON.stringify(text)};
    </script>
  </body>
</html>`;

await page.setContent(html, { waitUntil: "load" });

// Resize the viewport to exactly fit the rendered content, then take a
// normal (non-fullPage) screenshot. Chromium's CDP fullPage capture can
// fail with "Unable to capture screenshot" on large diagrams (a known
// Playwright/Chromium bug); a viewport-sized capture is a single bounded
// call and doesn't hit it.
const box = await page.evaluate(() => ({
  width: Math.ceil(document.body.scrollWidth),
  height: Math.ceil(document.body.scrollHeight),
}));
await page.setViewportSize({
  width: Math.max(1, box.width),
  height: Math.max(1, box.height),
});
await page.screenshot({ path: output });
await browser.close();
console.log(`Rendered ${input} -> ${output}`);
