import { chromium } from "playwright";
import { readFile } from "node:fs/promises";

const input = process.argv[2] ?? "oneshot/c3_example.txt";
const output = process.argv[3] ?? "oneshot/c3_example_playwright.png";
const text = await readFile(input, "utf8");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  deviceScaleFactor: 2,
});

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <style>
      :root {
        color-scheme: light;
      }
      body {
        margin: 0;
        background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 100%);
        padding: 32px;
        font-family: Menlo, Monaco, "Cascadia Mono", "Segoe UI Mono", monospace;
      }
      .frame {
        display: inline-block;
        background: #ffffff;
        border: 1px solid #d9e1ea;
        border-radius: 14px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        padding: 24px 28px;
      }
      pre {
        margin: 0;
        color: #111827;
        font-size: 22px;
        line-height: 1.22;
        letter-spacing: 0;
        white-space: pre;
      }
    </style>
  </head>
  <body>
    <div class="frame"><pre></pre></div>
    <script>
      document.querySelector("pre").textContent = ${JSON.stringify(text)};
    </script>
  </body>
</html>`;

await page.setContent(html, { waitUntil: "load" });
const frame = page.locator(".frame");
await frame.screenshot({ path: output });
await browser.close();
console.log(`Rendered ${input} -> ${output} via Playwright`);
