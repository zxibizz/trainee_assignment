#!/usr/bin/env python3
"""Package the current repository into a single archive for submission.

Cross-platform (Windows / macOS / Linux) — only requires Python 3.
Candidates run this and email the resulting .tar.gz to HR, so nothing has to
live on a public GitHub repository.

Usage:
    python package_submission.py "John Doe"
    python package_submission.py "John Doe" --output-dir ./out

The archive excludes generated / local-only artifacts (virtualenvs, caches,
the SQLite database, git history, stored tokens, etc.) so only the actual
source and docs are shipped.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
import tarfile
from datetime import datetime
from pathlib import Path

# Directory names and glob patterns to keep out of the archive. These are
# generated locally or contain secrets/history and should not travel with a
# submission.
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}
EXCLUDED_FILE_PATTERNS = (
    "*.pyc",
    "*.egg-info",
    "*.db",
    ".DS_Store",
    ".products_cli_tokens.json",
    ".tokens.json",
    ".env",
    "products-cli-challenge-*.tar.gz",
)


def slugify(name: str) -> str:
    """Turn a candidate name into a filename-safe slug."""
    slug = name.strip().lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9._-]", "", slug)
    return slug


def is_excluded_file(filename: str) -> bool:
    return any(fnmatch.fnmatch(filename, pat) for pat in EXCLUDED_FILE_PATTERNS)


def iter_files(repo_dir: Path):
    """Yield files under ``repo_dir``, skipping excluded dirs and files."""
    for root, dirs, files in os.walk(repo_dir):
        # Prune excluded directories in place so os.walk doesn't descend them.
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for filename in files:
            if is_excluded_file(filename):
                continue
            yield Path(root) / filename


def build_archive(repo_dir: Path, archive_path: Path) -> None:
    repo_name = repo_dir.name
    archive_resolved = archive_path.resolve()
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in iter_files(repo_dir):
            # Never include the archive itself if it's written inside the repo.
            if file_path.resolve() == archive_resolved:
                continue
            arcname = Path(repo_name) / file_path.relative_to(repo_dir)
            tar.add(file_path, arcname=str(arcname))


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "K", "M", "G"):
        if size < 1024 or unit == "G":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}G"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="package_submission.py",
        description="Package this repository into a single archive to email to HR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example:\n  python package_submission.py "John Doe"',
    )
    parser.add_argument(
        "candidate_name",
        metavar="CANDIDATE_NAME",
        help='Your full name, e.g. "John Doe" (used in the archive filename).',
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory to write the archive to (default: the current directory).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    slug = slugify(args.candidate_name)
    if not slug:
        print(
            'error: candidate name is empty after sanitising; e.g. use "John Doe"',
            file=sys.stderr,
        )
        return 1

    repo_dir = Path(__file__).resolve().parent
    repo_name = repo_dir.name

    output_dir = (
        Path(args.output_dir).expanduser().resolve() if args.output_dir else Path.cwd()
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_name = f"{repo_name}-{slug}-{timestamp}.tar.gz"
    archive_path = output_dir / archive_name

    print(f"Packaging '{repo_name}' for candidate '{args.candidate_name}'...")
    build_archive(repo_dir, archive_path)

    size = human_size(archive_path.stat().st_size)
    print()
    print("Created submission archive:")
    print(f"  {archive_path}  ({size})")
    print()
    print("Send this file to HR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
