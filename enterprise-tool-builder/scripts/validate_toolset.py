"""
Run validation checks across a generated tool directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_tool import SDK_PYTHON, SUPPORTED_SDKS, emit
from lint_tools import ToolLinter


def iter_python_files(tools_dir: Path) -> list[Path]:
    """List Python files for compile checks."""
    return sorted(path for path in tools_dir.rglob("*.py") if path.is_file())


def compile_python_files(tools_dir: Path) -> list[str]:
    """Compile Python files in memory and return syntax errors."""
    errors: list[str] = []
    for path in iter_python_files(tools_dir):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except UnicodeDecodeError:
            try:
                source = path.read_text(encoding="cp1252")
                compile(source, str(path), "exec")
            except Exception as exc:
                errors.append(f"{path}: {exc}")
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    return errors


def validate_toolset(tools_dir: Path, sdk: str) -> dict[str, Any]:
    """Run linting and any SDK-specific structural checks."""
    if not tools_dir.exists():
        raise FileNotFoundError(f"Tools directory not found: {tools_dir}")

    linter = ToolLinter(str(tools_dir), sdk=sdk)
    lint_results = linter.lint_all_tools()
    compile_errors = compile_python_files(tools_dir) if sdk == SDK_PYTHON else []

    return {
        "success": not lint_results and not compile_errors,
        "sdk": sdk,
        "tools_dir": str(tools_dir),
        "lint": linter.generate_report(lint_results),
        "compile_errors": compile_errors,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Validate a generated enterprise tool directory.",
        epilog=(
            "Examples:\n"
            "  python scripts/validate_toolset.py --tools-dir generated_tools --sdk python\n"
            "  python scripts/validate_toolset.py --tools-dir generated_tools_ts --sdk typescript"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tools-dir",
        default="generated_tools",
        help="Path to the generated tool directory",
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
    """Render validation output."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return

    if payload["success"]:
        print("toolset validation passed")
        return

    print("toolset validation failed")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = validate_toolset(Path(args.tools_dir), sdk=args.sdk)
        emit_result(result, args.format)
        return 0 if result["success"] else 1
    except FileNotFoundError as exc:
        emit(str(exc))
        return 2
    except ValueError as exc:
        emit(f"Error: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        emit(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
