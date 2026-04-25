#!/usr/bin/env python3
"""Fix test coverage gaps by generating test stubs.

Usage:
    python scripts/fix_coverage.py [--generate]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.agents.skills.test_stub_agent import TestStubAgent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auto-generate test stubs for uncovered functions")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--generate", action="store_true", help="Generate test files")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    agent = TestStubAgent()
    result = agent.run(project_root=str(root), generate=args.generate)

    print(f"Functions scanned: {result['total_functions']}")
    print(f"Tested functions: {result['tested_functions']}")
    print(f"Coverage: {result['coverage_ratio']:.1%}")
    print(f"Gaps found: {result['gaps_found']}")

    if result['gaps']:
        print("\nCoverage gaps:")
        for gap in result['gaps'][:20]:
            print(f"  {gap['source_file']}::{gap['symbol_name']} -> {gap['test_file']}")
        if len(result['gaps']) > 20:
            print(f"  ... and {len(result['gaps']) - 20} more")

    if args.generate:
        print(f"\nGenerated stubs: {result['stubs_generated']}")
    else:
        print("\n(Dry run — use --generate to create test files)")

    return 0 if result['gaps_found'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
