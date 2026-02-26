# CLAUDE.md

## Project Overview
Python 3.14 toolkit for bundling Roam Research markdown exports with their
Cloud Firestore-hosted images into self-contained `.mdbundle` directories.

## Setup
```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Key Commands
```bash
bundle-roam-md -m <file> -p <port> -g <graph> -t <token> -o <output_dir>

# Run the full check pipeline (format + lint + type check + tests) in one shot:
hatch run check

# Individual steps (run in this order):
pydocstringformatter --write src/ # reflow docstring content (PEP 257)
ruff format --preview src/        # fix structural formatting around docstrings
ruff check --fix src/ tests/      # lint + fix docstring style (Google convention)
black .                           # format code
pyright                           # type check (strict)
pytest                            # run tests
```

## Project Structure
- `src/roam_pub/` — main package
  - `bundle_roam_md.py` — CLI entry point (Typer app)
  - `roam_md_bundle.py` — core bundling logic
  - `roam_local_api.py` — ApiEndpointURL model for the Roam Local API
  - `roam_asset.py` — Cloud Firestore asset fetching
  - `roam_model.py`, `roam_page.py`, `roam_transcribe.py` — in progress
- `tests/fixtures/` — sample markdown, images, JSON for tests

## Conventions
- Src layout: package lives under `src/roam_pub/`
- Line length: 120 chars (Black + Ruff)
- Docstrings: PEP 257 format (pydocstringformatter), Google style convention (Ruff)
- Tests: pytest, files named `test_*.py`
- **Strong typing**: all Python code must use type annotations throughout; no `Any` types; enforced by pyright in strict mode

## Modern Python Requirements (Python 3.14)
All code written or modified by Claude MUST follow these conventions — no exceptions:

- **Built-in generics**: always `list[x]`, `tuple[x, y]`, `dict[k, v]`, `set[x]` — never `List`, `Tuple`, `Dict`, `Set` from `typing`
- **Union syntax**: always `X | Y` and `X | None` — never `Union[X, Y]` or `Optional[X]`
- **Type aliases**: always `type Foo = ...` (PEP 695) — never `Foo: TypeAlias = ...` or bare `Foo = ...`
- **No `from __future__ import annotations`**: not needed in Python 3.14 (PEP 649 deferred evaluation is the default)
- **No string-quoted forward references**: never `"ClassName"` in annotations; if a forward reference is needed, reorder definitions so the referenced name is declared first
- **No `cast()`**: never use `typing.cast()`; fix the type properly instead
- **No `Any`**: never use `typing.Any`; use a precise type or a type variable

## Environment Variables (referenced by `bundle_roam_md.py` CLI args)
- `ROAM_LOCAL_API_PORT` — port for Roam Local API
- `ROAM_GRAPH_NAME` — Roam graph name
- `ROAM_API_TOKEN` — bearer token for auth
- `ROAM_CACHE_DIR` — directory for caching downloaded Cloud Firestore assets
