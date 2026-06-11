from html.parser import HTMLParser
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


def test_project_citation_is_fully_italicized():
    """Check complete citation strings render in one emphasized block."""
    citation = build_site.render_citation("Author. (2026). Complete citation.")

    assert (
        citation
        == '            <p class="citation"><em>Author. (2026). Complete citation.</em></p>'
    )


def test_page_uses_research_overview_framing():
    """Check the page has moved beyond the old conference framing."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()

    assert "Evaluation of Explainable AI for Time Series" in parser.headings
    assert "Class-dependent evaluation effects" in parser.headings
    assert "Computational metrics and human understanding" in parser.headings
    assert "Tools for controlled evaluation" in parser.headings
    assert "Research overview" in html
    assert "Conference focus" not in html
    assert "Class-dependent evaluation of time-series explanations" not in parser.headings


def test_topbar_has_concise_navigation_and_portrait():
    """Check the topbar carries concise page navigation and a personal cue."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()

    assert "Paper 1 open version" not in html
    assert "Paper 2 open version" not in html
    assert "View the papers/projects" not in html
    assert 'class="hero-actions"' not in html
    assert ">Computational</a>" in html
    assert ">Human</a>" in html
    assert ">Tools</a>" in html
    assert ">Scholar</a>" in html
    assert 'class="brand-portrait"' in html
    assert 'class="researcher-portrait"' not in html
    assert any(image.get("src") == "assets/profile-pic-round.png" for image in parser.images)


def test_hero_includes_decorative_heatmap_visual():
    """Check the hero shows a decorative heatmap below the intro."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()
    hero_copy = html.split('<div class="hero-copy">', maxsplit=1)[1].split("</div>", maxsplit=1)[0]

    assert 'class="hero-visual"' in html
    assert hero_copy.index('class="intro"') < hero_copy.index('class="hero-visual"')
    assert any(
        image.get("src") == "assets/hero/fig_example_ts_hm.png"
        and image.get("class") == "hero-heatmap"
        and image.get("aria-hidden") == "true"
        for image in parser.images
    )


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


def test_section_backgrounds_stay_neutral_while_project_borders_keep_color():
    """Check section bands are neutral and project cards keep color accents."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    section_muted_rule = css.split(".section-muted {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "background: var(--section-muted)" in section_muted_rule
    assert "var(--yellow-soft)" not in section_muted_rule
    assert "var(--green-soft)" not in section_muted_rule
    assert ".project-featured:first-of-type" in css
    assert ".project-featured:nth-of-type(2)" in css
    assert ".project-single" in css
    assert ".tool-project" in css


def test_section_background_alternation_starts_after_hero():
    """Check generated section backgrounds alternate from the first section."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    content = build_site.load_site(ROOT / "content" / "site.yaml")

    assert '<section class="section section-lead section-muted" id="papers">' in html
    assert '<section class="section" id="metrics">' in html
    assert '<section class="section section-muted" id="tool">' in html
    assert all(
        "section-muted" not in section.get("classes", [])
        for section in content["sections"]
    )


def test_project_figure_surfaces_are_neutral():
    """Check figure frames avoid tinted backgrounds that compete with plots."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    gallery_frame_rule = css.split(".gallery-frame {", maxsplit=1)[1].split("}", maxsplit=1)[0]
    figure_stack_rule = css.split(".project-figure-stack {", maxsplit=1)[1].split("}", maxsplit=1)[
        0
    ]

    assert "background: var(--surface)" in gallery_frame_rule
    assert "background: var(--surface)" in figure_stack_rule
    assert "linear-gradient" not in gallery_frame_rule
    assert "linear-gradient" not in figure_stack_rule
    assert "var(--green-soft)" not in figure_stack_rule


def test_footer_includes_subtle_ai_disclaimer():
    """Check the footer includes a compact AI coding tools note."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")

    assert "This website was generated with the help of AI coding tools." in html
    assert ".ai-disclaimer" in css


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
        "https://scholar.google.com/citations?hl=en&user=bhR-GboAAAAJ&view_op=list_works&sortby=pubdate",
    }

    assert expected_links.issubset(set(parser.links))
    assert "Open access" not in html
    assert html.count(">arXiv</a>") == 3


def test_readme_documents_website_generation_workflow():
    """Check README explains how to edit, regenerate, test, and deploy."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Website Generation" in readme
    assert "content/site.yaml" in readme
    assert "assets/<project-slug>/" in readme
    assert "uv run python scripts/build_site.py" in readme
    assert "uv run pytest -q" in readme
    assert "No server-side build step is required on GitHub Pages." in readme
