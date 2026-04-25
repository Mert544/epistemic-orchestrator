#!/usr/bin/env python3
"""Fix missing docstrings across the Apex codebase.

Usage:
    python scripts/fix_docstrings.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.agents.skills.docstring_agent import DocstringAgent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auto-fix missing docstrings")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Show gaps without patching")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    agent = DocstringAgent()
    result = agent.run(project_root=str(root), patch=not args.dry_run)

    print(f"Symbols scanned: {result['total_symbols']}")
    print(f"Gaps found: {result['gaps_found']}")
    print(f"Files patched: {len(result['patched_files'])}")

    if result['gaps']:
        print("\nMissing docstrings:")
        for gap in result['gaps'][:20]:
            print(f"  {gap['file']}:{gap['line']} {gap['symbol_type']} '{gap['name']}'")
        if len(result['gaps']) > 20:
            print(f"  ... and {len(result['gaps']) - 20} more")

    if args.dry_run:
        print("\n(Dry run — no files modified)")
    else:
        print(f"\nPatched files: {result['patched_files']}")

    return 0 if result['gaps_found'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
