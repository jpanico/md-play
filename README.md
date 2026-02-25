# roam-pub

Python 3.14 toolkit for bundling Roam Research markdown exports with their Firebase-hosted images into self-contained `.mdbundle` directories.

## Development Setup

### Prerequisites

- Python 3.14 or higher
- Git

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/roam-pub.git
   cd roam-pub
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package in editable mode with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

   This installs:
   - The `roam-pub` package in editable mode (changes to code are immediately reflected)
   - Runtime dependencies: `pydantic`, `requests`, `typer`
   - Development dependencies: `pytest`, `black`, `pyright`

### Running Tests

Once the development environment is set up, run the full test suite with pytest:

```bash
pytest
```

To run tests with verbose output:
```bash
pytest -v
```

To run a specific test file:
```bash
pytest tests/test_roam_asset.py
```

#### Live Integration Tests

Some tests require the Roam Desktop app to be running locally. These are marked with `@pytest.mark.live` and are skipped by default. To enable them:

```bash
export ROAM_LIVE_TESTS=1
pytest -m live
```

### Code Formatting

This project uses [Black](https://black.readthedocs.io/) for code formatting (line length: 120):

```bash
black .
```

To check formatting without making changes:
```bash
black --check .
```

### Docstring Linting

[Ruff](https://docs.astral.sh/ruff/) enforces Google-style docstrings:

```bash
ruff check src/ tests/
ruff check --fix src/ tests/   # auto-fix
```

### Type Checking

[Pyright](https://github.com/microsoft/pyright) is configured in **strict** mode for `src/`:

```bash
pyright
```

All production code under `src/roam_pub/` must be fully annotated with no `Any` types. Test modules (`tests/`) use `basic` type checking (`# pyright: basic` directive at the top of each test file).

## Project Structure

```
roam-pub/
├── src/
│   └── roam_pub/                  # Main package
│       ├── __init__.py
│       ├── bundle_roam_md.py      # CLI entry point (Typer app)
│       ├── roam_md_bundle.py      # Core bundling logic
│       ├── roam_asset.py          # Firebase asset fetching
│       ├── roam_model.py          # Pydantic data model + FetchRoamSchema
│       ├── roam_page.py           # FetchRoamPage — Datalog page queries
│       └── roam_transcribe.py     # (in progress)
├── tests/                         # pytest test suite
│   ├── fixtures/                  # Sample markdown, images, JSON
│   ├── test_bundle_roam_md_cli.py
│   ├── test_roam_asset.py
│   ├── test_roam_md_bundle.py
│   ├── test_roam_model.py
│   ├── test_roam_page.py
│   └── test_roam_transcribe.py
├── scripts/
│   ├── setup-mdbundle-handler.sh   # Setup .mdbundle auto-open in Typora
│   └── refresh-mdbundle-folders.sh # Refresh existing .mdbundle folders
├── docs/
│   ├── MDBUNDLE_SETUP.md           # macOS .mdbundle integration guide
│   ├── roam-local-api.md           # Roam Local API (JSON over HTTP) reference
│   ├── roam-querying.md            # Datalog query language and query reference
│   ├── roam-schema.md              # Full Roam attribute schema from a live graph
│   ├── roam_database.png           # Datomic/DataScript datom model diagram
│   └── test_article_children.png   # Example page screenshot used in docs
├── bundle-roam-md.sh               # Shell wrapper for direct execution
├── pyproject.toml                  # Project configuration
└── README.md
```

## Usage

### Running the Bundle Script

The package provides the `bundle-roam-md` command-line utility for bundling Roam Research markdown files with their Firebase-hosted images.

**Method 1: Using the installed command (recommended)**

After installing the package with `pip install -e ".[dev]"`, you can use the installed command with named arguments:

```bash
bundle-roam-md --markdown-file <file> --port <port> --graph <name> --token <token> --output <dir>
```

Example with long flags:
```bash
bundle-roam-md --markdown-file my_notes.md --port 3333 --graph SCFH --token your-bearer-token --output ./output
```

Example with short flags:
```bash
bundle-roam-md -m my_notes.md -p 3333 -g SCFH -t your-bearer-token -o ./output
```

**Using Environment Variables**

To avoid passing sensitive tokens on the command line, you can use environment variables:

```bash
export ROAM_LOCAL_API_PORT=3333
export ROAM_GRAPH_NAME=SCFH
export ROAM_API_TOKEN=your-bearer-token

# Now you can omit these flags
bundle-roam-md -m my_notes.md -o ./output
```

Supported environment variables:
- `ROAM_LOCAL_API_PORT` — Port for Roam Local API
- `ROAM_GRAPH_NAME` — Name of the Roam graph
- `ROAM_API_TOKEN` — Bearer token for authentication

Command-line arguments always override environment variables.

**Method 2: Using the shell wrapper script**

For direct execution without activating the virtual environment:

```bash
./bundle-roam-md.sh --markdown-file <file> --port <port> --graph <name> --token <token> --output <dir>
```

Example:
```bash
./bundle-roam-md.sh -m my_notes.md -p 3333 -g SCFH -t your-bearer-token -o ./output
```

**Getting help:**

```bash
bundle-roam-md --help
# or
./bundle-roam-md.sh --help
```

### What it does

The script:
1. Reads a Roam Research markdown file
2. Finds all Firebase-hosted images (`firebasestorage.googleapis.com` URLs)
3. Fetches each image via the Roam Local API
4. Saves images locally in a `.mdbundle` directory
5. Updates the markdown file with local image references
6. Performs cleanup: normalizes link text and removes escaped brackets

### Output

Creates a directory named `<markdown_file>.mdbundle/` containing:
- Updated markdown file with local image references
- All downloaded images

### macOS Integration: Auto-Open in Typora

To configure macOS to automatically open `.mdbundle` folders in Typora when double-clicked:

1. **Run the setup script:**
   ```bash
   ./scripts/setup-mdbundle-handler.sh
   ```

   This creates and registers `OpenMDBundle.app` which handles `.mdbundle` folders.

2. **Refresh existing .mdbundle folders (if any):**
   ```bash
   ./scripts/refresh-mdbundle-folders.sh ~/wip
   ```

   This updates the metadata for existing `.mdbundle` folders so macOS recognizes them properly.

3. **Done!** Double-clicking any `.mdbundle` folder will now open the markdown file in Typora

**How it works:**
- Double-clicking a `.mdbundle` folder launches `OpenMDBundle.app`
- The app uses AppleScript to properly handle the "open" event from macOS
- It extracts the markdown filename and opens it in Typora

**Troubleshooting:**
- If double-clicking doesn't work, try logging out and back in
- Right-click a `.mdbundle` folder → Get Info to verify "OpenMDBundle" appears under "Open with:"
- If it doesn't appear, run `mdimport <folder>` to force macOS to recognize it
- Test from command line: `open ~/path/to/your.mdbundle` should open in Typora

See [docs/MDBUNDLE_SETUP.md](docs/MDBUNDLE_SETUP.md) for detailed instructions and troubleshooting.

## Documentation

- [docs/roam-local-api.md](docs/roam-local-api.md) — Roam Local API reference (JSON over HTTP)
- [docs/roam-querying.md](docs/roam-querying.md) — Datalog query language, query structure, and all queries used in this project
- [docs/roam-schema.md](docs/roam-schema.md) — Full Roam attribute schema retrieved from a live graph
- [docs/MDBUNDLE_SETUP.md](docs/MDBUNDLE_SETUP.md) — macOS `.mdbundle` integration guide

## License

TBD
