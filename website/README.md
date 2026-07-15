# Website

Static website source for the published benchmark site.

## Layout

- `index.html`: main landing page
- `404.html`: GitHub Pages fallback redirect
- `pages/`: secondary pages such as the setup guide
- `assets/css/`: shared styles
- `assets/js/`: browser-side page logic
- `assets/data/`: generated site data consumed by the UI
- `tools/`: local build helpers for website data generation

## Build

```bash
node website/tools/build_site_data.mjs
python3 -m http.server 8000 -d website
```

## GitHub Pages

This site is deployed from the repository through GitHub Actions.

- Workflow: `.github/workflows/deploy-pages.yml`
- Published artifact root: `website/`
- Generated metadata: `website/assets/data/site_data.json`

To publish:

1. Enable `GitHub Actions` as the Pages source in the repository settings.
2. Push to `main` or run the `Deploy Website` workflow manually.
