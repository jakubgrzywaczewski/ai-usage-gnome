# Contributing

Thanks for considering a contribution to AI Usage.

## Development setup

```bash
sudo apt install gir1.2-appindicator3-0.1 gir1.2-notify-0.7 \
    libsecret-1-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0

python -m venv --system-site-packages .venv   # so system PyGObject is visible
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the app from source:

```bash
python -m ai_usage.main
```

## Before opening a pull request

```bash
pytest          # the domain/provider logic is GTK-free and must stay tested
ruff check .    # lint
```

Both also run in CI on every push and pull request.

## Guidelines

- Branch off `main`; `main` is protected and merges through pull requests.
- Keep changes focused. One concern per pull request.
- Match the surrounding style: type hints, `from __future__ import annotations`,
  small functions. `ruff format` reflects the intended formatting.
- Provider APIs are undocumented and change without notice. When you adjust a
  parser, add a test with a captured payload (`tests/test_providers.py`).
- User-facing strings go through `ai_usage/domain/localization.py` and need both
  an English and a Polish entry — `tests/test_localization.py` enforces this.
- Update `CHANGELOG.md` under `## [Unreleased]`.

## Releasing (maintainers)

1. Move `## [Unreleased]` notes into a new version section in `CHANGELOG.md`.
2. Bump `__version__` in `ai_usage/__init__.py` and `version` in `setup.py`.
3. Commit, tag `vX.Y.Z`, push with `--follow-tags`.
4. `gh release create vX.Y.Z --verify-tag --notes "..."`.
