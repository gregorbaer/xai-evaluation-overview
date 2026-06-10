from pathlib import Path


def find_project_root() -> Path:
    """
    Locate the root directory of the current project.

    Traverses up the directory tree from the current file's location (or current
    working directory if running in a notebook) until it finds a directory containing
    one of the project markers: .git, README.md, or pyproject.toml.
    In notebooks, falls back to Path.cwd() since __file__ may not exist.

    Returns:
        Path: The absolute path to the project root directory.
    """
    # Works in normal scripts; in notebooks __file__ may not exist
    start = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd().resolve()

    # Walk up until we find a project marker
    for p in [start, *start.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Could not find project root from current location.")
