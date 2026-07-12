import { readFile } from "node:fs/promises";
import { chromium } from "playwright";

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  console.error("Usage: node scripts/renderers/render_ascii.mjs <input.ascii> <output.png>");
  process.exit(1);
}

const text = await readFile(input, "utf8");

const browser = await chromium.launch({ headless: true });
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
await page.locator("pre").screenshot({ path: output });
await browser.close();
console.log(`Rendered ${input} -> ${output}`);
