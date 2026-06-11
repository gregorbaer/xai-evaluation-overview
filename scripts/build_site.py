"""Generate the static GitHub Pages HTML from editable YAML content."""

from __future__ import annotations

import argparse
import difflib
from html import escape
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "content" / "site.yaml"
OUTPUT_PATH = ROOT / "index.html"
FOOTER_ICONS = {
    "github": (
        '<svg class="footer-icon" aria-hidden="true" viewBox="0 0 24 24" role="img">'
        '<path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 '
        '10.91.58.11.79-.25.79-.56v-2.01c-3.2.7-3.87-1.54-3.87-1.54'
        '-.52-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.71.08-.71 1.16.08 '
        '1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73'
        '-1.55-2.55-.29-5.23-1.28-5.23-5.68 0-1.25.45-2.28 1.19-3.08-.12'
        '-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18.92-.26 1.91-.38 '
        '2.89-.39.98 0 1.97.13 2.89.39 2.2-1.49 3.17-1.18 3.17-1.18.63 '
        '1.58.23 2.75.11 3.04.74.8 1.19 1.83 1.19 3.08 0 4.41-2.69 '
        '5.38-5.25 5.67.42.36.78 1.08.78 2.18v3.23c0 .31.21.68.8.56A10.51 '
        '10.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"/></svg>'
    ),
    "linkedin": (
        '<svg class="footer-icon" aria-hidden="true" viewBox="0 0 24 24" role="img">'
        '<path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.86 '
        '0-2.14 1.45-2.14 2.95v5.66H9.34V9h3.42v1.56h.05c.48-.9 1.64'
        '-1.85 3.37-1.85 3.61 0 4.28 2.38 4.28 5.47v6.27zM5.32 '
        '7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.1 '
        '20.45H3.54V9H7.1v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.72v20.56'
        'C0 23.23.79 24 1.77 24h20.46c.98 0 1.77-.77 '
        '1.77-1.72V1.72C24 .77 23.21 0 22.23 0z"/></svg>'
    ),
    "scholar": (
        '<svg class="footer-icon" aria-hidden="true" viewBox="0 0 24 24" role="img" '
        'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" '
        'stroke-width="2"><path d="M3 8.5 12 4l9 4.5-9 4.5L3 8.5Z"/>'
        '<path d="M7 11v4.5c1.1 1.35 2.75 2 5 2s3.9-.65 5-2V11"/>'
        '<path d="M21 8.5V15"/></svg>'
    ),
}


def main() -> int:
    """Run the site generator command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether index.html matches the generated output.",
    )
    args = parser.parse_args()

    site = load_site(CONTENT_PATH)
    rendered = render_site(site)

    if args.check:
        return check_output(rendered, OUTPUT_PATH)

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    return 0


def load_site(path: Path) -> dict[str, Any]:
    """Load the structured site content from YAML.

    Args:
        path: Path to the YAML content file.

    Returns:
        Parsed site content.
    """
    with path.open(encoding="utf-8") as stream:
        content = yaml.safe_load(stream)

    if not isinstance(content, dict):
        raise TypeError(f"{path} must contain a mapping at the top level.")

    return content


def check_output(rendered: str, output_path: Path) -> int:
    """Check whether the committed HTML matches generated output.

    Args:
        rendered: Generated HTML.
        output_path: Existing HTML path to compare against.

    Returns:
        Process exit code.
    """
    current = output_path.read_text(encoding="utf-8")
    if current == rendered:
        return 0

    diff = difflib.unified_diff(
        current.splitlines(),
        rendered.splitlines(),
        fromfile=str(output_path),
        tofile="generated index.html",
        lineterm="",
    )
    print("index.html is out of date. Run: uv run python scripts/build_site.py", file=sys.stderr)
    print("\n".join(diff), file=sys.stderr)
    return 1


def render_site(content: dict[str, Any]) -> str:
    """Render the full static HTML document.

    Args:
        content: Parsed YAML site content.

    Returns:
        Complete HTML document.
    """
    site = content["site"]
    lines = [
        "<!doctype html>",
        f'<html lang="{attr(site.get("language", "en"))}">',
        "  <head>",
        '    <meta charset="utf-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"    <title>{text(site['title'])}</title>",
        "    <meta",
        '      name="description"',
        f'      content="{attr(site["description"])}"',
        "    >",
        '    <link rel="stylesheet" href="styles.css">',
        "  </head>",
        "  <body>",
        render_header(content),
        "",
        "    <main>",
        *[render_section(section, index) for index, section in enumerate(content["sections"])],
        "    </main>",
        "",
        render_footer(content["footer"]),
        render_gallery_script(),
        "  </body>",
        "</html>",
        "",
    ]
    return "\n".join(lines)


def render_header(content: dict[str, Any]) -> str:
    """Render the top navigation and hero.

    Args:
        content: Parsed YAML site content.

    Returns:
        Header HTML.
    """
    brand = content["brand"]
    portrait = brand["portrait"]
    hero = content["hero"]
    nav_links = "\n".join(
        f'          <a href="{attr(item["href"])}">{text(item["label"])}</a>'
        for item in content["nav"]
    )
    hero_actions = render_link_row(
        hero.get("actions", []),
        "hero-actions",
        "Primary links",
        indent=10,
    )
    portrait_attrs = {
        "class": "brand-portrait",
        "src": portrait["src"],
        "alt": portrait.get("alt", ""),
        "aria-hidden": "true" if portrait.get("hidden") else None,
    }
    hero_visual = render_hero_visual(hero.get("visual"))

    return "\n".join(
        [
            '    <header class="site-header">',
            '      <nav class="topbar" aria-label="Page sections">',
            f'        <a class="brand" href="{attr(brand["href"])}">',
            f"          <img{render_attrs(portrait_attrs)}>",
            f"          <span>{text(brand['name'])}</span>",
            "        </a>",
            '        <div class="nav-links">',
            nav_links,
            "        </div>",
            "      </nav>",
            "",
            f'      <section class="hero" id="{attr(hero["id"])}">',
            '        <div class="hero-copy">',
            f'          <p class="eyebrow">{text(hero["eyebrow"])}</p>',
            f"          <h1>{text(hero['title'])}</h1>",
            f'          <p class="intro">{text(hero["intro"])}</p>',
            hero_visual,
            *([hero_actions] if hero_actions else []),
            "        </div>",
            "      </section>",
            "    </header>",
        ]
    )


def render_hero_visual(visual: dict[str, Any] | None) -> str:
    """Render an optional decorative hero image.

    Args:
        visual: Image metadata, or None when the hero has no visual.

    Returns:
        Hero visual HTML or an empty string.
    """
    if not visual:
        return ""

    image_attrs = {
        "class": "hero-heatmap",
        "src": visual["src"],
        "alt": visual.get("alt", ""),
        "aria-hidden": "true" if visual.get("hidden") else None,
    }
    return "\n".join(
        [
            '          <figure class="hero-visual">',
            f"            <img{render_attrs(image_attrs)}>",
            "          </figure>",
        ]
    )


def render_section(section: dict[str, Any], index: int) -> str:
    """Render a content section and its projects.

    Args:
        section: Section content.
        index: Zero-based section index after the hero.

    Returns:
        Section HTML.
    """
    section_classes = ["section", *section.get("classes", [])]
    if index % 2 == 0:
        section_classes.append("section-muted")
    project_blocks = [render_project(project) for project in section["projects"]]
    return "\n".join(
        [
            f'      <section class="{attr(" ".join(section_classes))}" id="{attr(section["id"])}">',
            '        <div class="section-heading">',
            '          <div class="section-title">',
            f'            <p class="eyebrow">{text(section["eyebrow"])}</p>',
            f"            <h2>{text(section['title'])}</h2>",
            "          </div>",
            f"          <p>{text(section['description'])}</p>",
            "        </div>",
            "",
            "\n\n".join(project_blocks),
            "      </section>",
            "",
        ]
    )


def render_project(project: dict[str, Any]) -> str:
    """Render one project card.

    Args:
        project: Project content.

    Returns:
        Project HTML.
    """
    project_classes = ["project", *project.get("classes", [])]
    body = "\n".join(f"            <p>{text(paragraph)}</p>" for paragraph in project["body"])
    citation = render_citation(project.get("citation"))
    link_row = render_link_row(project["links"], "link-row", None, indent=12)
    visual = render_project_visual(project)

    parts = [
        f'        <article class="{attr(" ".join(project_classes))}">',
        '          <div class="project-copy">',
        f'            <p class="tag">{text(project["tag"])}</p>',
        f"            <h3>{text(project['title'])}</h3>",
        f'            <p class="takeaway">{text(project["takeaway"])}</p>',
        body,
    ]
    if citation:
        parts.append(citation)
    parts.extend(
        [
            link_row,
            "          </div>",
            visual,
            "        </article>",
        ]
    )
    return "\n".join(parts)


def render_citation(citation: str | None) -> str:
    """Render a project citation as an emphasized formatted string.

    Args:
        citation: Complete formatted citation, or None when no citation should render.

    Returns:
        Citation paragraph HTML or an empty string.
    """
    if not citation:
        return ""

    return (
        '            <p class="citation">'
        f"<em>{text(citation)}</em></p>"
    )


def render_link_row(
    links: list[dict[str, str]],
    class_name: str,
    aria_label: str | None,
    indent: int,
) -> str:
    """Render a row of styled links.

    Args:
        links: Link definitions with labels, URLs, and optional styles.
        class_name: CSS class for the containing row.
        aria_label: Optional accessible label for the row.
        indent: Number of spaces to prepend to each generated line.

    Returns:
        Link row HTML.
    """
    spaces = " " * indent
    label_attr = f' aria-label="{attr(aria_label)}"' if aria_label else ""
    if not links:
        return ""

    lines = [f'{spaces}<div class="{attr(class_name)}"{label_attr}>']
    for link in links:
        style = link.get("style", "secondary")
        lines.append(
            f'{spaces}  <a class="button {attr(style)}" href="{attr(link["href"])}">'
            f'{text(link["label"])}</a>'
        )
    lines.append(f"{spaces}</div>")
    return "\n".join(lines)


def render_gallery(slug: str, figures: list[dict[str, str]]) -> str:
    """Render a stable project figure gallery.

    Args:
        slug: Stable project identifier used for gallery controls.
        figures: Figure metadata.

    Returns:
        Figure/gallery HTML.
    """
    first = figures[0]
    has_multiple_figures = len(figures) > 1
    has_caption = any(figure.get("caption", "").strip() for figure in figures)
    first_caption = first.get("caption", "").strip()
    lines = [
        '          <figure class="project-visual">',
        f'            <div class="project-gallery" data-gallery-id="{attr(slug)}">',
        '              <div class="gallery-frame">',
        (
            '                <img class="gallery-main-image"'
            f' src="{attr(first["src"])}" alt="{attr(first["alt"])}">'
        ),
        "              </div>",
    ]

    if has_caption:
        hidden = " hidden" if not first_caption else ""
        lines.append(
            f'              <figcaption class="gallery-caption"{hidden}>'
            f"{text(first_caption)}</figcaption>"
        )

    if has_multiple_figures:
        lines.extend(render_gallery_thumbnails(slug, figures))

    lines.extend(
        [
            "            </div>",
            "          </figure>",
        ]
    )
    return "\n".join(lines)


def render_project_visual(project: dict[str, Any]) -> str:
    """Render a project's visual block.

    Args:
        project: Project content with figure metadata.

    Returns:
        Visual block HTML.
    """
    if project.get("figure_display") == "stack":
        return render_figure_stack(project["slug"], project["figures"])

    return render_gallery(project["slug"], project["figures"])


def render_figure_stack(slug: str, figures: list[dict[str, str]]) -> str:
    """Render all project figures together in one stable visual block.

    Args:
        slug: Stable project identifier.
        figures: Figure metadata.

    Returns:
        Stacked figure HTML.
    """
    lines = [
        '          <figure class="project-visual">',
        f'            <div class="project-figure-stack" data-figure-stack-id="{attr(slug)}">',
    ]
    for figure in figures:
        lines.extend(
            [
                '              <div class="stacked-figure">',
                f'                <img src="{attr(figure["src"])}" alt="{attr(figure["alt"])}">',
            ]
        )
        caption = figure.get("caption", "").strip()
        if caption:
            lines.append(
                f'                <figcaption class="gallery-caption">{text(caption)}</figcaption>'
            )
        lines.append("              </div>")

    lines.extend(
        [
            "            </div>",
            "          </figure>",
        ]
    )
    return "\n".join(lines)


def render_gallery_thumbnails(slug: str, figures: list[dict[str, str]]) -> list[str]:
    """Render thumbnail controls for a multi-figure gallery.

    Args:
        slug: Stable project identifier used for gallery controls.
        figures: Figure metadata.

    Returns:
        Thumbnail control HTML lines.
    """
    lines = ['              <div class="gallery-thumbs" aria-label="Project figures">']
    for index, figure in enumerate(figures):
        aria_current = "true" if index == 0 else "false"
        label = f"Show figure {index + 1}"
        lines.extend(
            [
                (
                    '                <button class="gallery-thumb" type="button"'
                    f' aria-label="{attr(label)}" aria-current="{aria_current}"'
                    f' data-gallery-target="{attr(slug)}"'
                    f' data-gallery-src="{attr(figure["src"])}"'
                    f' data-gallery-alt="{attr(figure["alt"])}"'
                    f' data-gallery-caption="{attr(figure.get("caption", "").strip())}">'
                ),
                (
                    f'                  <img src="{attr(figure["src"])}" alt=""'
                    ' aria-hidden="true">'
                ),
                "                </button>",
            ]
        )
    lines.append("              </div>")
    return lines


def render_footer(footer: dict[str, Any]) -> str:
    """Render the site footer.

    Args:
        footer: Footer content.

    Returns:
        Footer HTML.
    """
    footer_links = "\n".join(
        render_footer_link(link, indent=8)
        for link in footer["links"]
    )
    return "\n".join(
        [
            '    <footer class="site-footer">',
            '      <div class="footer-meta">',
            f"        <p>{text(footer['text'])}</p>",
            f'        <p class="ai-disclaimer">{text(footer["disclaimer"])}</p>',
            "      </div>",
            '      <div class="footer-links">',
            footer_links,
            "      </div>",
            "    </footer>",
        ]
    )


def render_footer_link(link: dict[str, str], indent: int) -> str:
    """Render a footer link with an optional icon and visible text.

    Args:
        link: Footer link definition.
        indent: Number of spaces to prepend to the generated line.

    Returns:
        Footer link HTML.
    """
    spaces = " " * indent
    icon = render_footer_icon(link.get("icon"))
    label = f'<span class="footer-link-label">{text(link["label"])}</span>'

    return f'{spaces}<a href="{attr(link["href"])}">{icon}{label}</a>'


def render_footer_icon(icon_name: str | None) -> str:
    """Render a decorative footer icon.

    Args:
        icon_name: Icon identifier from the footer link metadata.

    Returns:
        Inline SVG icon HTML, or an empty string when no icon is set.

    Raises:
        ValueError: If the icon name is not supported.
    """
    if not icon_name:
        return ""

    try:
        return FOOTER_ICONS[icon_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported footer icon: {icon_name}") from exc


def render_gallery_script() -> str:
    """Render the small progressive-enhancement gallery script.

    Returns:
        Inline JavaScript for thumbnail-driven image swapping.
    """
    return """    <script>
      for (const thumbnail of document.querySelectorAll(".gallery-thumb")) {
        thumbnail.addEventListener("click", () => {
          const gallery = document.querySelector(
            `[data-gallery-id="${thumbnail.dataset.galleryTarget}"]`,
          );
          const image = gallery?.querySelector(".gallery-main-image");
          const caption = gallery?.querySelector(".gallery-caption");

          if (!gallery || !image) {
            return;
          }

          image.src = thumbnail.dataset.gallerySrc;
          image.alt = thumbnail.dataset.galleryAlt;

          if (caption) {
            const nextCaption = thumbnail.dataset.galleryCaption || "";
            caption.textContent = nextCaption;
            caption.hidden = nextCaption === "";
          }

          for (const other of gallery.querySelectorAll(".gallery-thumb")) {
            other.setAttribute("aria-current", String(other === thumbnail));
          }
        });
      }
    </script>"""


def render_attrs(attributes: dict[str, str | None]) -> str:
    """Render HTML attributes, omitting values set to None.

    Args:
        attributes: Attribute names and values.

    Returns:
        String beginning with a space when attributes are present.
    """
    rendered = [f'{name}="{attr(value)}"' for name, value in attributes.items() if value is not None]
    if not rendered:
        return ""
    return " " + " ".join(rendered)


def text(value: str) -> str:
    """Escape text content for HTML.

    Args:
        value: Raw text.

    Returns:
        Escaped HTML text.
    """
    return escape(str(value), quote=False)


def attr(value: str) -> str:
    """Escape an attribute value for HTML.

    Args:
        value: Raw attribute value.

    Returns:
        Escaped HTML attribute value.
    """
    return escape(str(value), quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
