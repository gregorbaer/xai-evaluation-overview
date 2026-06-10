# xai-evaluation-overview

This repository contains a build-free one-page GitHub Pages site for a curated
research overview on evaluating explainable AI methods for time-series models.

The public page is [`index.html`](index.html), with styles in
[`styles.css`](styles.css) and local figures in [`assets/`](assets). GitHub Pages
can serve the site directly from the repository root on the `main` branch.

## Editing

- Edit page content in `index.html`.
- Edit the visual theme in `styles.css`.
- Keep local figures in `assets/`.
- Use `writing_guidelines.md` as the tone guide for future copy edits.

## Testing

Run the static checks with:

```bash
uv run pytest -q
```

The tests cover page structure, local asset references, internal anchors, image
alt text, and the expected DOI, arXiv, documentation, GitHub, and Scholar links.

## GitHub Pages

In the repository settings on GitHub:

1. Open **Pages**.
2. Set the source to **Deploy from a branch**.
3. Select branch **main** and folder **/**.

After deployment, the page should be available at:

```text
https://gregorbaer.github.io/xai-evaluation-overview/
```
