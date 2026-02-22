"""Backward-compatible shim for local runs/tests.

Prefer importing `markitdown_server.main` directly.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from markitdown_server.main import app, run  # noqa: E402


if __name__ == "__main__":
    run()
