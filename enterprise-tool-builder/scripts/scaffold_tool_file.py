"""
Scaffold a generated tool package for Python, TypeScript, or JavaScript.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_tool import SDK_PYTHON, SUPPORTED_SDKS, emit, slugify


def write_text(path: Path, content: str, dry_run: bool) -> None:
    """Write file content unless dry-run is enabled."""
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def python_pyproject(service: str) -> str:
    """Return a minimal Python project file."""
    return "\n".join(
        [
            "[project]",
            f'name = "{service}-tools"',
            'version = "0.1.0"',
            'description = "Generated LangChain enterprise tools"',
            'requires-python = ">=3.11"',
            "dependencies = [",
            '  "langchain>=1.0.0",',
            '  "pydantic>=2.7.0",',
            "]",
            "",
        ]
    )


def node_package_json(service: str, sdk: str) -> str:
    """Return a minimal Node package manifest."""
    dev_dependencies = (
        {
            "typescript": "^5.7.0",
            "tsx": "^4.19.0",
            "@types/node": "^22.10.0",
        }
        if sdk == "typescript"
        else {}
    )
    payload = {
        "name": f"{service}-tools",
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "lint": "node -e \"console.log('Add project-specific linting here')\"",
        },
        "dependencies": {
            "langchain": "^1.0.0",
            "zod": "^3.24.0",
        },
    }
    if dev_dependencies:
        payload["devDependencies"] = dev_dependencies
    return json.dumps(payload, indent=2)


def auth_flow_stub(service: str) -> str:
    """Return an auth flow placeholder file."""
    return "\n".join(
        [
            f"# {service} auth flow",
            "",
            "Fill in the real credential acquisition steps for this generated tool package.",
            "",
            "Required details:",
            "- auth type",
            "- token or credential source",
            "- environment variables",
            "- tenant or workspace identifiers",
            "",
        ]
    )


class ToolFileScaffold:
    """Create a generated tool package skeleton."""

    def __init__(self, base_dir: str = "generated_tools"):
        self.base_dir = Path(base_dir)

    def scaffold(self, service: str, package_name: str | None, sdk: str, dry_run: bool) -> dict[str, Any]:
        """Create the package structure for one service."""
        package = slugify(package_name or service, fallback="service_tools")
        service_dir = self.base_dir / package

        created: list[str] = []

        if sdk == SDK_PYTHON:
            directories = [
                service_dir / "tools",
                service_dir / "auth",
                service_dir / "tests",
                service_dir / "utils",
            ]
            files = {
                service_dir / "__init__.py": '"""Generated enterprise tool package."""\n',
                service_dir / "tools" / "__init__.py": '"""Generated LangChain tools."""\n',
                service_dir / "auth" / "__init__.py": '"""Authentication helpers."""\n',
                service_dir / "tests" / "__init__.py": '"""Test package."""\n',
                service_dir / "utils" / "__init__.py": '"""Shared utilities."""\n',
                service_dir / "pyproject.toml": python_pyproject(package),
                service_dir / "auth_flow.md": auth_flow_stub(service),
            }
        else:
            entry_file = "index.ts" if sdk == "typescript" else "index.js"
            directories = [
                service_dir / "src" / "tools",
                service_dir / "src" / "auth",
                service_dir / "src" / "utils",
                service_dir / "tests",
            ]
            files = {
                service_dir / "package.json": node_package_json(package, sdk),
                service_dir / "src" / entry_file: 'export * from "./tools/index.js";\n',
                service_dir / "src" / "tools" / entry_file: "",
                service_dir / "auth_flow.md": auth_flow_stub(service),
            }
            if sdk == "typescript":
                files[service_dir / "tsconfig.json"] = json.dumps(
                    {
                        "compilerOptions": {
                            "target": "ES2022",
                            "module": "NodeNext",
                            "moduleResolution": "NodeNext",
                            "strict": True,
                            "declaration": True,
                            "outDir": "dist",
                        },
                        "include": ["src/**/*.ts", "tests/**/*.ts"],
                    },
                    indent=2,
                )

        for directory in directories:
            created.append(str(directory))
            if not dry_run:
                directory.mkdir(parents=True, exist_ok=True)

        for path, content in files.items():
            created.append(str(path))
            write_text(path, content, dry_run=dry_run)

        return {
            "success": True,
            "service": service,
            "package_name": package,
            "sdk": sdk,
            "dry_run": dry_run,
            "root": str(service_dir),
            "created": created,
        }


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Scaffold a generated enterprise tool package.",
        epilog=(
            "Examples:\n"
            "  python scripts/scaffold_tool_file.py jira --sdk python\n"
            "  python scripts/scaffold_tool_file.py slack --sdk typescript --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("service", help="Service name, such as jira or slack")
    parser.add_argument("--package-name", help="Optional package/folder name override")
    parser.add_argument(
        "--sdk",
        choices=SUPPORTED_SDKS,
        default=SDK_PYTHON,
        help="Target LangChain SDK",
    )
    parser.add_argument(
        "--base-dir",
        default="generated_tools",
        help="Directory where generated tool packages live",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the scaffold plan without writing files",
    )
    return parser


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Render CLI results."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return
    print(f"scaffolded {payload['sdk']} package at {payload['root']}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        scaffold = ToolFileScaffold(base_dir=args.base_dir)
        result = scaffold.scaffold(
            service=args.service,
            package_name=args.package_name,
            sdk=args.sdk,
            dry_run=args.dry_run,
        )
        emit_result(result, args.format)
        return 0
    except ValueError as exc:
        emit(f"Error: {exc}")
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        emit(f"Unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
