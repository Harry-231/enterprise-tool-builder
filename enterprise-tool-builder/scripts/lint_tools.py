"""
Lint generated LangChain tool files for basic structural quality.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from generate_tool import SDK_PYTHON, SUPPORTED_SDKS, emit


def read_text(path: Path) -> str:
    """Read text from mixed-encoding generated files."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode file: {path}")


class ToolLinter:
    """Lint LangChain tool drafts by SDK."""

    def __init__(self, tools_dir: str = "generated_tools", sdk: str = SDK_PYTHON):
        self.tools_dir = Path(tools_dir)
        self.sdk = sdk

    def tool_files(self) -> list[Path]:
        """List candidate tool files."""
        extension = {SDK_PYTHON: ".py", "typescript": ".ts", "javascript": ".js"}[self.sdk]
        return sorted(path for path in self.tools_dir.rglob(f"*{extension}") if path.is_file())

    def lint_tool_file(self, filepath: Path) -> list[str]:
        """Return issues for one tool file."""
        content = read_text(filepath)
        issues: list[str] = []

        if self.sdk == SDK_PYTHON:
            if '"""' not in content:
                issues.append("missing module docstring")
            if "@tool" not in content:
                issues.append("missing @tool decorator")
            if "BaseModel" not in content:
                issues.append("missing Pydantic args schema")
            if "success" not in content or "metadata" not in content:
                issues.append("missing stable response envelope")
            if "TODO" not in content:
                issues.append("missing implementation placeholder note")
        else:
            if 'import { tool } from "langchain";' not in content:
                issues.append("missing langchain tool import")
            if 'import * as z from "zod";' not in content:
                issues.append("missing zod schema import")
            if "schema: z.object" not in content and "const schema = z.object" not in content:
                issues.append("missing zod object schema")
            if "success:" not in content or "metadata:" not in content:
                issues.append("missing stable response envelope")
            if "TODO" not in content:
                issues.append("missing implementation placeholder note")

        return issues

    def lint_all_tools(self) -> dict[str, list[str]]:
        """Lint every tool file under the configured directory."""
        files = self.tool_files()
        results: dict[str, list[str]] = {}

        for file_path in files:
            issues = self.lint_tool_file(file_path)
            if issues:
                results[str(file_path)] = issues

        return results

    def generate_report(self, lint_results: dict[str, list[str]]) -> dict[str, Any]:
        """Return structured lint report data."""
        return {
            "success": not lint_results,
            "sdk": self.sdk,
            "tools_dir": str(self.tools_dir),
            "files_with_issues": len(lint_results),
            "issues": lint_results,
        }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI args."""
    parser = argparse.ArgumentParser(
        description="Lint generated LangChain tool files for one SDK target.",
        epilog=(
            "Examples:\n"
            "  python scripts/lint_tools.py --tools-dir generated_tools --sdk python\n"
            "  python scripts/lint_tools.py --tools-dir generated_tools_ts --sdk typescript"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tools-dir",
        default="generated_tools",
        help="Directory containing generated tools",
    )
    parser.add_argument(
        "--sdk",
        choices=SUPPORTED_SDKS,
        default=SDK_PYTHON,
        help="Target LangChain SDK",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    return parser


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Write results to stdout."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return

    if payload["success"]:
        print("lint passed")
        return

    print(f"lint found issues in {payload['files_with_issues']} file(s)")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        linter = ToolLinter(tools_dir=args.tools_dir, sdk=args.sdk)
        results = linter.lint_all_tools()
        report = linter.generate_report(results)
        emit_result(report, args.format)
        return 0 if report["success"] else 1
    except ValueError as exc:
        emit(f"Error: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        emit(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
