# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Setup

This is a Python 3.14 project using a virtual environment.

```bash
# Activate the virtual environment
source .venv/bin/activate

# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt
```

## Scripts

### roam_convert.py

Converts Roam Research Markdown to standard Markdown:
- Adds H1 header with the original filename
- Converts root-level bullets to H2 headers

```bash
# Basic usage (creates input_converted.md)
python roam_convert.py input.md

# Specify output file
python roam_convert.py input.md -o output.md
```
