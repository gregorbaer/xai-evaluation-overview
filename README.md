# xai-evaluation-overview

This repository contains a generated one-page GitHub Pages site for a curated
research overview on evaluating explainable AI methods for time-series models.

The public page is [`index.html`](index.html), with styles in
[`styles.css`](styles.css), editable content in [`content/site.yaml`](content/site.yaml),
and local figures in [`assets/`](assets). GitHub Pages serves the generated
`index.html` directly from the repository root on the `main` branch.

## Editing

- Edit page content, links, and figure metadata in `content/site.yaml`.
- Edit the visual theme in `styles.css`.
- Keep local project figures in `assets/<project-slug>/`.
- Use `writing_guidelines.md` as the tone guide for future copy edits.

## Website Generation

Manual website changes use the YAML source and then regenerate the committed
HTML page:

1. Edit text, links, sections, projects, and figure lists in `content/site.yaml`.
2. Add or replace local figures in the relevant `assets/<project-slug>/` folder.
3. Reference each figure path from the project `figures` list in YAML. Figure
   `caption` fields are optional; omit them or leave them empty to show no
   caption space.
4. Regenerate the static page:

```bash
uv run python scripts/build_site.py
```

5. Check the result locally by opening `index.html` in a browser.
6. Run the tests:

```bash
uv run pytest -q
```

7. Commit the YAML, generated `index.html`, styles, scripts, tests, and assets.

## Testing

Run the static checks with:

```bash
uv run pytest -q
```

The tests cover page structure, local asset references, internal anchors, image
alt text, and the expected DOI, arXiv, documentation, GitHub, and Scholar links.
They also check that the committed `index.html` matches the YAML-generated
output.

## GitHub Pages

In the repository settings on GitHub:

1. Open **Pages**.
2. Set the source to **Deploy from a branch**.
3. Select branch **main** and folder **/**.

For normal deployments:

1. Push the committed generated `index.html` to `main`.
2. GitHub Pages serves the repository root.
3. No server-side build step is required on GitHub Pages.

After deployment, the page should be available at:

```text
https://gregorbaer.github.io/xai-evaluation-overview/
```
