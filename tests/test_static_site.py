from html import unescape
from html.parser import HTMLParser
import re
import struct
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402


class SiteParser(HTMLParser):
    """Collects the small amount of HTML structure needed by the tests."""

    def __init__(self):
        """Initialize empty collections for parsed page data."""
        super().__init__()
        self.ids = set()
        self.links = []
        self.images = []
        self.headings = []
        self.buttons = []
        self._current_heading = None

    def handle_starttag(self, tag, attrs):
        """Record IDs, links, images, and heading starts."""
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a":
            self.links.append(attributes.get("href", ""))
        if tag == "img":
            self.images.append(attributes)
        if tag == "button":
            self.buttons.append(attributes)
        if tag in {"h1", "h2", "h3"}:
            self._current_heading = []

    def handle_data(self, data):
        """Collect heading text while inside a heading element."""
        if self._current_heading is not None:
            self._current_heading.append(data)

    def handle_endtag(self, tag):
        """Store normalized heading text when a heading ends."""
        if tag in {"h1", "h2", "h3"} and self._current_heading is not None:
            self.headings.append(" ".join("".join(self._current_heading).split()))
            self._current_heading = None


def parse_site():
    """Parse the root GitHub Pages file."""
    parser = SiteParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    return parser


def test_committed_site_is_generated_from_yaml_source():
    """Check the committed HTML matches the editable YAML content source."""
    assert (ROOT / "content" / "site.yaml").exists()
    assert (ROOT / "scripts" / "build_site.py").exists()

    result = subprocess.run(
        ["uv", "run", "python", "scripts/build_site.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_project_citations_are_single_editable_strings():
    """Check citations can be edited as complete formatted strings."""
    content = build_site.load_site(ROOT / "content" / "site.yaml")

    citations = [
        project.get("citation")
        for section in content["sections"]
        for project in section["projects"]
        if project.get("citation")
    ]

    assert citations
    assert all(isinstance(citation, str) for citation in citations)


def test_project_citation_renders_as_collapsible_cite():
    """Check full citations sit behind a small collapsible Cite toggle."""
    citation = build_site.render_citation("Author. (2026). Complete citation.")

    assert citation.strip().startswith('<details class="cite">')
    assert "<summary>Cite</summary>" in citation
    assert "Author. (2026). Complete citation." in citation
    assert build_site.render_citation(None) == ""

def test_page_uses_research_overview_framing():
    """Check the page has moved beyond the old conference framing."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()

    assert "Evaluation of Explainable AI" in parser.headings
    assert "Evaluation of Explainable AI for Time Series" not in parser.headings
    assert "Class-dependent evaluation effects" in parser.headings
    assert "Computational metrics and human understanding" in parser.headings
    assert "Tools for controlled evaluation" in parser.headings
    assert "Conference focus" not in html
    assert "Class-dependent evaluation of time-series explanations" not in parser.headings


def test_topbar_has_concise_navigation_and_portrait():
    """Check the topbar carries concise page navigation and a personal cue."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()
    topbar_html = html.split('<nav class="topbar"', maxsplit=1)[1].split("</nav>", maxsplit=1)[0]

    assert "Paper 1 open version" not in html
    assert "Paper 2 open version" not in html
    assert "View the papers/projects" not in html
    assert 'class="hero-actions"' not in html
    assert ">Computational</a>" in topbar_html
    assert ">Human</a>" in topbar_html
    assert ">Tools</a>" in topbar_html
    assert ">Scholar</a>" not in topbar_html
    assert 'class="brand-portrait"' in html
    assert 'class="researcher-portrait"' not in html
    assert any(image.get("src") == "assets/profile-pic-round.png" for image in parser.images)


def test_hero_has_no_decorative_visual_or_eyebrow():
    """Check the hero is reduced to title and intro."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="hero-visual"' not in html
    assert "fig_example_ts_hm.png" not in html
    assert not hasattr(build_site, "render_hero_visual")


def test_header_band_padding_stays_compact():
    """Check the header band keeps modest padding around topbar and hero."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    desktop_css, mobile_css = css.split("@media (max-width: 800px) {", maxsplit=1)
    topbar_rule = desktop_css.split(".topbar {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    hero_rule = desktop_css.split(".hero {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    mobile_hero_rule = mobile_css.split(".hero {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    def paddings(rule):
        return [int(value) for value in re.findall(r"\d+", re.search(r"padding: ([^;]+);", rule).group(1))]

    assert max(paddings(topbar_rule)) <= 14
    assert max(paddings(hero_rule)) <= 36
    assert max(paddings(mobile_hero_rule)) <= 32


def test_decorative_labels_and_takeaway_boxes_are_removed():
    """Check eyebrow labels, project tags, and takeaway boxes no longer render."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="eyebrow"' not in html
    assert 'class="tag"' not in html
    assert 'class="takeaway"' not in html
    assert 'class="button' not in html


def test_projects_use_byline_and_description_fields():
    """Check YAML projects carry a byline and a description, without old fields."""
    content = build_site.load_site(ROOT / "content" / "site.yaml")
    projects = [project for section in content["sections"] for project in section["projects"]]

    assert projects
    for project in projects:
        assert project.get("byline", "").strip(), project["slug"]
        assert project.get("description"), project["slug"]
        assert all(isinstance(paragraph, str) for paragraph in project["description"])
        for old_field in ("tag", "takeaway", "body"):
            assert old_field not in project, (project["slug"], old_field)



def test_project_text_precedes_figure():
    """Check each project renders head, then description text, then the figure."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    articles = html.split('<article class="project"')[1:]

    assert len(articles) == 4
    assert 'class="lede"' not in html
    for article in articles:
        article = article.split("</article>", maxsplit=1)[0]
        head = article.index('class="project-head"')
        copy = article.index('class="project-copy"')
        visual = article.index('class="project-visual"')
        assert head < copy < visual
        head_html = article[head:copy]
        assert "<h3>" in head_html
        assert 'class="byline"' in head_html



def test_styles_avoid_shadows_and_rounded_frames():
    """Check frames are square and flat; only the portrait stays round."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", css)

    assert "box-shadow" not in css
    rounded = [selector.strip() for selector, body in rules if "border-radius" in body]
    assert rounded == [".brand-portrait"]

def test_generator_supports_thumbnail_galleries_for_future_projects():
    """Check multi-figure gallery rendering stays available for future projects."""
    gallery = build_site.render_gallery(
        "future-project",
        [
            {"src": "assets/future-project/fig1.png", "alt": "First figure.", "caption": "One."},
            {"src": "assets/future-project/fig2.png", "alt": "Second figure.", "caption": "Two."},
        ],
    )

    assert 'class="project-gallery"' in gallery
    assert "data-gallery-target=" in gallery
    assert 'class="gallery-caption"' in gallery
    assert gallery.count('class="gallery-thumb"') == 2


def test_empty_gallery_captions_do_not_reserve_space():
    """Check empty captions can be omitted or hidden in generated galleries."""
    no_captions = build_site.render_gallery(
        "captionless-project",
        [{"src": "assets/captionless-project/fig1.png", "alt": "Captionless figure."}],
    )
    mixed_captions = build_site.render_gallery(
        "mixed-caption-project",
        [
            {"src": "assets/mixed-caption-project/fig1.png", "alt": "First figure.", "caption": ""},
            {
                "src": "assets/mixed-caption-project/fig2.png",
                "alt": "Second figure.",
                "caption": "Two.",
            },
        ],
    )

    assert 'class="gallery-caption"' not in no_captions
    assert 'class="gallery-caption" hidden' in mixed_captions


def test_xaitimesynth_keeps_logo_and_example_visible_together():
    """Check the tool card keeps both original visuals visible at once."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    tool_html = html.split('data-figure-stack-id="xaitimesynth"', maxsplit=1)[1].split(
        "</figure>",
        maxsplit=1,
    )[0]

    assert 'class="project-figure-stack"' in html
    assert "xaitimesynth_logo.svg" in tool_html
    assert "quickstart_dataset.png" in tool_html
    assert 'class="gallery-thumb"' not in tool_html


def test_section_overviews_are_full_width_stacked_blocks():
    """Check section intros stack title and description at project-card width."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    section_heading_rule = css.split(".section-heading {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "width: 100%" in section_heading_rule
    assert "grid-template-columns" not in section_heading_rule



def test_page_shell_uses_shared_gutter():
    """Check content and the full-bleed header/footer bands share one side gutter."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    root_rule = css.split(":root {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    page_shell_rule = css.split("\nmain {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    band_rule = css.split(".site-header,\n.site-footer {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "--page-gutter: 16px" in root_rule
    assert "100% - var(--page-gutter) - var(--page-gutter)" in page_shell_rule
    assert "padding-inline: max(var(--page-gutter)" in band_rule


def test_header_and_footer_are_charcoal_bands_with_white_text():
    """Check header and footer share a charcoal band with white text on a warm page."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    root_rule = css.split(":root {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    band_rule = css.split(".site-header,\n.site-footer {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    paper = re.search(r"--paper:\s*(#[0-9a-fA-F]+)", root_rule).group(1).lower()

    assert paper not in {"#fff", "#ffffff", "#fbfaf7"}
    assert "--band: #2a2e33" in root_rule
    assert "--band-heading: #ffffff" in root_rule
    assert "background: var(--band)" in band_rule
    html_rule = css.split("\nhtml {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert "background: var(--band)" in html_rule, "overscroll below footer stays charcoal"


def test_project_figure_surfaces_are_neutral():
    """Check figures sit on plain white surfaces without tinted backgrounds."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    gallery_image_rule = css.split(".gallery-main-image {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    figure_stack_rule = css.split(".project-figure-stack {", maxsplit=1)[1].split("}", maxsplit=1)[
        0
    ]

    assert "background: var(--surface)" in gallery_image_rule
    assert "background: var(--surface)" in figure_stack_rule
    assert "padding: var(--figure-mat)" in gallery_image_rule, "white margin around figure edges"
    assert "--figure-mat:" in css.split(":root {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert "linear-gradient" not in css



def test_desktop_figures_are_compact_previews_beside_text():
    """Check desktop figures are short previews placed beside the description."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    desktop_css = css.split("@media (max-width: 800px) {", maxsplit=1)[0]
    project_rule = desktop_css.split(".project {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    frame_rule = desktop_css.split(".gallery-frame {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    max_height = re.search(r"height: clamp\([^,]+,[^,]+,\s*(\d+)px\)", frame_rule)

    assert '"copy visual"' in project_rule
    assert max_height and int(max_height.group(1)) <= 320


def test_mobile_gallery_figures_can_shrink_to_screen_width():
    """Check mobile figures fit the screen width with a height cap for tall figures."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    mobile_rule = css.split("@media (max-width: 800px) {", maxsplit=1)[1]
    gallery_frame_rule = mobile_rule.split(".gallery-frame {", maxsplit=1)[1].split(
        "}",
        maxsplit=1,
    )[0]
    gallery_image_rule = mobile_rule.split(".gallery-main-image {", maxsplit=1)[1].split(
        "}",
        maxsplit=1,
    )[0]

    max_height = re.search(r"max-height: (\d+)px", gallery_image_rule)

    assert "height: auto" in gallery_frame_rule
    assert "max-width: 100%" in gallery_image_rule
    assert "height: auto" in gallery_image_rule
    assert max_height and int(max_height.group(1)) <= 340, "tall figures need a mobile cap"


def test_header_band_colors_come_from_band_tokens():
    """Check every header color is a band token, so a theme swap only edits :root."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    root_rule = css.split(":root {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    nav_rule = css.split(".nav-links a {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    for token in ("--band:", "--band-heading:", "--band-text:", "--band-muted:", "--band-rule:"):
        assert token in root_rule, token
    assert "color: var(--band-muted)" in nav_rule



def test_footer_is_a_single_slim_line():
    """Check the footer drops the AI note and keeps compact vertical padding."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    content = build_site.load_site(ROOT / "content" / "site.yaml")
    footer_rule = re.search(r"(?m)(?<!,\n)^\.site-footer \{([^}]*)\}", css).group(1)
    padding = re.search(r"padding-block: (\d+)px(?: (\d+)px)?", footer_rule)

    assert "AI coding tools" not in html
    assert "ai-disclaimer" not in css
    assert "disclaimer" not in content["footer"]
    assert padding and all(int(value) <= 20 for value in padding.groups() if value)


def test_footer_links_include_icons_and_visible_labels():
    """Check profile links keep recognizable icons without becoming icon-only."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    footer_links = html.split('<div class="footer-links">', maxsplit=1)[1].split(
        "</div>",
        maxsplit=1,
    )[0]

    assert footer_links.count('class="footer-icon"') == 3
    assert footer_links.count('aria-hidden="true"') >= 3
    assert footer_links.count('width="18"') == 3
    assert footer_links.count('height="18"') == 3
    assert '<span class="footer-link-label">Google Scholar</span>' in footer_links
    assert '<span class="footer-link-label">GitHub</span>' in footer_links
    assert '<span class="footer-link-label">LinkedIn</span>' in footer_links


def test_footer_icons_are_normalized_from_local_svg_assets():
    """Check footer icons come from local SVG assets and inherit text color."""
    assert set(build_site.FOOTER_ICON_PATHS) == {"github", "linkedin", "scholar"}
    for icon_path in build_site.FOOTER_ICON_PATHS.values():
        assert icon_path.exists()

        icon = build_site.normalize_footer_icon(icon_path)

        assert 'class="footer-icon"' in icon
        assert 'width="18"' in icon
        assert 'height="18"' in icon
        assert 'aria-hidden="true"' in icon
        assert 'fill="currentColor"' in icon
        assert "#000000" not in icon


def test_expected_sections_exist():
    """Check the major GitHub Pages sections are present."""
    parser = parse_site()

    assert {"top", "papers", "metrics", "tool"}.issubset(parser.ids)


def test_local_assets_referenced_by_page_exist():
    """Check local image and stylesheet references point to real files."""
    parser = parse_site()
    local_paths = ["styles.css"]
    local_paths.extend(
        image["src"] for image in parser.images if not urlparse(image.get("src", "")).scheme
    )

    assert local_paths
    for relative_path in local_paths:
        assert (ROOT / relative_path).exists(), relative_path


def test_local_figures_are_grouped_by_project_folder():
    """Check local project figures use extendable per-project asset folders."""
    parser = parse_site()
    local_project_figures = [
        image["src"]
        for image in parser.images
        if image.get("src", "").startswith("assets/")
        and image.get("src") != "assets/profile-pic-round.png"
    ]

    assert local_project_figures
    for relative_path in local_project_figures:
        assert len(Path(relative_path).parts) >= 3, relative_path


def test_internal_anchor_links_point_to_real_sections():
    """Check same-page links point to existing section IDs."""
    parser = parse_site()
    anchors = [link[1:] for link in parser.links if link.startswith("#")]

    assert anchors
    assert set(anchors).issubset(parser.ids)


def test_images_have_alt_text():
    """Check all images include useful alt text."""
    parser = parse_site()

    assert parser.images
    for image in parser.images:
        if image.get("aria-hidden") == "true":
            continue
        assert image.get("alt", "").strip(), image


def test_expected_external_links_are_present():
    """Check the page keeps the main research and tool links easy to find."""
    parser = parse_site()
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    expected_links = {
        "https://doi.org/10.1007/978-3-032-08330-2_14",
        "https://arxiv.org/abs/2502.17022",
        "https://doi.org/10.1007/978-3-032-19105-2_27",
        "https://arxiv.org/abs/2506.11790",
        "https://doi.org/10.48550/arXiv.2603.25251",
        "https://arxiv.org/abs/2603.25251",
        "https://gregorbaer.github.io/xaitimesynth/",
        "https://github.com/gregorbaer/xaitimesynth",
        "https://arxiv.org/abs/2603.06781",
        "https://scholar.google.com/citations?hl=en&user=bhR-GboAAAAJ&view_op=list_works&sortby=pubdate",
        "https://www.linkedin.com/in/gregorbaer/",
    }

    assert expected_links.issubset(set(parser.links))
    assert "Open access" not in html
    assert html.count(">arXiv</a>") == 4


def test_readme_documents_website_generation_workflow():
    """Check README explains how to edit, regenerate, test, and deploy."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Website Generation" in readme
    assert "content/site.yaml" in readme
    assert "assets/<project-slug>/" in readme
    assert "uv run python scripts/build_site.py" in readme
    assert "uv run pytest -q" in readme
    assert "No server-side build step is required on GitHub Pages." in readme


def png_size(path):
    """Read a PNG's width and height from its IHDR chunk.

    Args:
        path: Path to a PNG file.

    Returns:
        Tuple of (width, height) in pixels.
    """
    header = Path(path).read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", header[16:24])


def test_page_has_open_graph_preview_tags():
    """Check link previews (LinkedIn etc.) get a title, description, and absolute image URL."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    head = html.split("</head>", maxsplit=1)[0]
    content = build_site.load_site(ROOT / "content" / "site.yaml")
    social = content["social"]

    def meta(attribute, name):
        match = re.search(rf'<meta {attribute}="{re.escape(name)}" content="([^"]*)">', head)
        assert match, name
        return unescape(match.group(1))

    assert social["url"].startswith("https://") and social["url"].endswith("/")
    assert meta("property", "og:type") == "website"
    assert meta("property", "og:title") == content["site"]["title"]
    assert meta("property", "og:description") == " ".join(content["site"]["description"].split())
    assert meta("property", "og:url") == social["url"]
    assert meta("property", "og:image") == social["url"] + social["image"]
    assert meta("property", "og:image:width") == "1200"
    assert meta("property", "og:image:height") == "627"
    assert meta("property", "og:image:alt") == social["image_alt"]
    assert meta("name", "twitter:card") == "summary_large_image"


def test_social_card_image_exists_with_linkedin_size():
    """Check the committed preview card is a 1200x627 PNG."""
    content = build_site.load_site(ROOT / "content" / "site.yaml")
    image = ROOT / content["social"]["image"]

    assert image.exists(), image
    assert png_size(image) == (1200, 627)


def test_social_card_figures_cover_each_project_once():
    """Check the card shows one figure per project, so it represents the breadth of work."""
    content = build_site.load_site(ROOT / "content" / "site.yaml")
    projects = [project for section in content["sections"] for project in section["projects"]]
    card_figures = content["social"]["card_figures"]

    owners = []
    for figure in card_figures:
        matches = [
            project["slug"]
            for project in projects
            if figure in {item["src"] for item in project["figures"]}
        ]
        assert len(matches) == 1, figure
        owners.append(matches[0])
        if not urlparse(figure).scheme:
            assert (ROOT / figure).exists(), figure

    assert sorted(owners) == sorted(project["slug"] for project in projects)
