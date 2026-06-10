from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    """Collects the small amount of HTML structure needed by the tests."""

    def __init__(self):
        """Initialize empty collections for parsed page data."""
        super().__init__()
        self.ids = set()
        self.links = []
        self.images = []
        self.headings = []
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


def test_page_uses_research_overview_framing():
    """Check the page has moved beyond the old conference framing."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()

    assert "Evaluation of Explainable AI for Time Series" in parser.headings
    assert "Class-dependent evaluation effects" in parser.headings
    assert "Metrics and human understanding" in parser.headings
    assert "Tools for controlled evaluation" in parser.headings
    assert "Research overview" in html
    assert "Conference focus" not in html
    assert "Class-dependent evaluation of time-series explanations" not in parser.headings


def test_hero_has_concise_project_actions_and_topbar_portrait():
    """Check the hero stays focused while the topbar keeps a personal cue."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = parse_site()

    assert "Paper 1 open version" not in html
    assert "Paper 2 open version" not in html
    assert "View the papers/projects" in html
    assert 'class="brand-portrait"' in html
    assert 'class="researcher-portrait"' not in html
    assert any(image.get("src") == "assets/profile-pic-round.png" for image in parser.images)


def test_section_overviews_are_full_width_stacked_blocks():
    """Check section intros stack title and description at project-card width."""
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    section_heading_rule = css.split(".section-heading {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "width: 100%" in section_heading_rule
    assert "grid-template-columns" not in section_heading_rule


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
