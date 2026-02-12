#!/usr/bin/env python3
"""
Script to bundle Roam Research Markdown files by fetching Firebase-hosted images
and replacing them with local file references.

Usage:
    python bundle_roam_md.py <markdown_file> <local_api_port> <graph_name>

Example:
    python bundle_roam_md.py my_notes.md 3333 SCFH
"""

import sys
import logging
from pathlib import Path

from mdplay.roam_md import process_markdown_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) != 4:
        print("Usage: python bundle_roam_md.py <markdown_file> <local_api_port> <graph_name>")
        print()
        print("Example:")
        print("  python bundle_roam_md.py my_notes.md 3333 SCFH")
        sys.exit(1)

    markdown_file: Path = Path(sys.argv[1])
    local_api_port: int = int(sys.argv[2])
    graph_name: str = sys.argv[3]

    try:
        process_markdown_file(markdown_file, local_api_port, graph_name)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
