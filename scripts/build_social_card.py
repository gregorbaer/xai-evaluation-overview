"""Render the 1200x627 social preview card (Open Graph image) with headless Chrome."""

from __future__ import annotations

import argparse
from html import escape
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_site  # noqa: E402

ROOT = build_site.ROOT
WIDTH, HEIGHT = 1200, 627
CHROME_NAMES = ("chromium", "chromium-browser", "google-chrome", "chrome-headless-shell")
PLAYWRIGHT_GLOB = "ms-playwright/*/chrome-headless-shell-linux64/chrome-headless-shell"

CARD_CSS = """
:root {
  --paper: #f3efe6;
  --surface: #ffffff;
  --line: #d8d1c4;
  --band: #2a2e33;
  --band-heading: #ffffff;
  --band-muted: #b4bcc5;
}
* { box-sizing: border-box; }
html, body { margin: 0; width: 1200px; height: 627px; overflow: hidden; }
body {
  display: grid;
  grid-template-columns: 480px 1fr;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
.panel {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 56px 44px;
  background: var(--band);
}
h1 {
  margin: 0 0 28px;
  color: var(--band-heading);
  font-family: "Source Serif 4", Georgia, serif;
  font-size: 58px;
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -0.01em;
}
.name {
  margin: 0;
  color: var(--band-muted);
  font-size: 24px;
}
.figures {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 16px;
  padding: 22px;
  background: var(--paper);
  min-width: 0;
  min-height: 0;
}
.cell {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: 0;
}
.cell img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  padding: 6px;
  border: 1px solid var(--line);
  background: var(--surface);
}
"""


def figure_url(source: str) -> str:
    """Resolve a card figure to a URL headless Chrome can load.

    Args:
        source: Local path relative to the repository root, or an absolute URL.

    Returns:
        The URL itself for remote figures, or a ``file://`` URL for local ones.

    Raises:
        FileNotFoundError: If a local figure does not exist.
    """
    if urlparse(source).scheme:
        return source
    path = ROOT / source
    if not path.exists():
        raise FileNotFoundError(path)
    return path.as_uri()


def render_card_html(content: dict) -> str:
    """Render the card as a self-contained HTML page.

    Args:
        content: Parsed YAML site content.

    Returns:
        HTML document sized to exactly 1200x627 pixels.
    """
    cells = "\n".join(
        f'    <div class="cell"><img src="{escape(figure_url(source))}" alt=""></div>'
        for source in content["social"]["card_figures"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
  <style>{CARD_CSS}</style>
</head>
<body>
  <div class="panel">
    <h1>{escape(content["hero"]["title"])}</h1>
    <p class="name">{escape(content["brand"]["name"])}</p>
  </div>
  <div class="figures">
{cells}
  </div>
</body>
</html>
"""


def find_chrome(explicit: str | None) -> str:
    """Locate a Chrome/Chromium binary for headless screenshots.

    Args:
        explicit: Binary path given on the command line, if any.

    Returns:
        Path to an executable Chrome binary.

    Raises:
        SystemExit: If no binary can be found.
    """
    candidates = [explicit, os.environ.get("CHROME")]
    candidates += [shutil.which(name) for name in CHROME_NAMES]
    candidates += [str(path) for path in sorted((Path.home() / ".cache").glob(PLAYWRIGHT_GLOB))]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit(
        "No Chrome/Chromium found. Pass --chrome PATH or set the CHROME environment variable."
    )


def main() -> int:
    """Render the social card PNG to the path configured in site.yaml."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", help="Path to a Chrome/Chromium binary.")
    args = parser.parse_args()

    content = build_site.load_site(build_site.CONTENT_PATH)
    output = ROOT / content["social"]["image"]
    output.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome(args.chrome)

    with tempfile.TemporaryDirectory() as tmp:
        card = Path(tmp) / "card.html"
        card.write_text(render_card_html(content), encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--no-sandbox",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--virtual-time-budget=6000",
                f"--window-size={WIDTH},{HEIGHT}",
                f"--screenshot={output}",
                card.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
