# Tooling

## First Steps After Cloning

1. Rename the project: Search for `repo-name` etc. connections (see below).
2. Run `make setup` to set up the environment and pre-commit hooks in one go.
3. Run pytests to ensure everything works: `uv run pytest -q`.

## Renaming The Template

When turning this template into a real project, rename these together:

1. Repository name, if desired
2. `name = "repo-name"` in `pyproject.toml`
3. `src/repo_name/`
4. `packages = ["src/repo_name"]` in `pyproject.toml`

Recommended convention:

- project/distribution name: `my-project`
- import package name: `my_project`

After renaming, refresh the environment:

```bash
uv lock
uv sync
```
