"""Compatibility CLI wrapper for parser CLI."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from malaysia_fsi.bank_statement.cli import parse_main


def main() -> int:
    return parse_main()


if __name__ == "__main__":
    sys.exit(main())
