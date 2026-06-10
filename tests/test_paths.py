from pathlib import Path

from repo_name.paths import find_project_root


def test_find_project_root_returns_repo_root():
    """
    Test that find_project_root returns the correct path to the project root.
    """
    root = find_project_root()
    expected_root = Path(__file__).resolve().parents[1]

    assert root == expected_root
    assert (root / "pyproject.toml").exists()
