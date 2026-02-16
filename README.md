# roam-pub

Markdown utilities for working with Roam Research exports.

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
   - Runtime dependencies: `pydantic`, `requests`
   - Development dependencies: `pytest`, `black`

### Running Tests

Once the development environment is set up, you can run tests using pytest:

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

### Code Formatting

This project uses Black for code formatting:

```bash
black .
```

To check formatting without making changes:
```bash
black --check .
```

## Project Structure

```
roam-pub/
├── src/
│   └── roam_pub/          # Main package code
│       ├── __init__.py
│       ├── roam_asset.py
│       ├── roam_md_bundle.py
│       └── bundle_roam_md.py
├── tests/                  # Test files
│   ├── test_roam_asset.py
│   └── test_roam_md_bundle.py
├── pyproject.toml          # Project configuration
└── README.md
```

## Scripts

The package provides the following command-line script:

- `bundle-roam-md`: Main utility for bundling Roam Research markdown files

## License

TBD
