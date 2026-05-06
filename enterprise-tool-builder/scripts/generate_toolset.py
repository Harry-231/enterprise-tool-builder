"""
Batch-generate LangChain tool drafts from endpoint schema files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_tool import (
    SDK_PYTHON,
    SUPPORTED_SDKS,
    ToolGenerator,
    emit,
    extract_endpoints,
    load_json_file,
    normalize_endpoint,
)


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Write CLI results."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return

    print(f"generated {payload['generated_count']} tool(s) for sdk={payload['sdk']}")


class ToolsetGenerator:
    """Generate full draft toolsets from endpoint bundles."""

    def __init__(self, schema_dir: str = "assets/endpoints", output_dir: str = "generated_tools"):
        self.schema_dir = Path(schema_dir)
        self.output_dir = Path(output_dir)
        self.generator = ToolGenerator(output_dir)

    def resolve_schema_files(self, service: str | None) -> list[Path]:
        """Return one or more endpoint schema files to process."""
        if service:
            explicit = self.schema_dir / f"{service}_endpoints.json"
            if not explicit.exists():
                raise FileNotFoundError(f"Schema file not found: {explicit}")
            return [explicit]

        files = sorted(self.schema_dir.glob("*_endpoints.json"))
        if not files:
            raise FileNotFoundError(f"No schema files found in {self.schema_dir}")
        return files

    def generate_toolset(
        self,
        service: str | None,
        sdk: str,
        endpoint_limit: int | None,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Generate draft tools across one or more schema files."""
        generated: list[dict[str, Any]] = []
        schema_files = self.resolve_schema_files(service)

        for schema_file in schema_files:
            schema = load_json_file(schema_file)
            service_key = str(schema.get("service_key") or schema_file.stem.replace("_endpoints", ""))
            endpoints = [normalize_endpoint(endpoint, service_key) for endpoint in extract_endpoints(schema)]

            if endpoint_limit is not None:
                endpoints = endpoints[:endpoint_limit]

            for endpoint in endpoints:
                code = self.generator.generate_tool_code(endpoint, sdk=sdk)
                extension = {SDK_PYTHON: ".py", "typescript": ".ts", "javascript": ".js"}[sdk]
                filename = f"{endpoint['id']}{extension}"
                if dry_run:
                    generated.append(
                        {
                            "schema_file": str(schema_file),
                            "endpoint_id": endpoint["id"],
                            "filename": filename,
                            "sdk": sdk,
                        }
                    )
                    continue

                output_path = self.generator.save_tool(code, filename)
                generated.append(
                    {
                        "schema_file": str(schema_file),
                        "endpoint_id": endpoint["id"],
                        "filename": filename,
                        "path": str(output_path),
                        "sdk": sdk,
                    }
                )

        return {
            "success": True,
            "sdk": sdk,
            "dry_run": dry_run,
            "generated_count": len(generated),
            "items": generated,
        }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI args."""
    parser = argparse.ArgumentParser(
        description="Generate LangChain tool drafts for a service or the full endpoint bundle.",
        epilog=(
            "Examples:\n"
            "  python scripts/generate_toolset.py --service github --sdk python --limit 5\n"
            "  python scripts/generate_toolset.py --service github --sdk typescript --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--schema-dir",
        default="assets/endpoints",
        help="Directory that contains bundled endpoint JSON files",
    )
    parser.add_argument("--service", help="Generate tools for one service key only")
    parser.add_argument(
        "--sdk",
        choices=SUPPORTED_SDKS,
        default=SDK_PYTHON,
        help="Target LangChain SDK",
    )
    parser.add_argument(
        "--output-dir",
        default="generated_tools",
        help="Directory where generated files are written",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum endpoints to generate per schema file",
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
        help="Preview generated filenames without writing files",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        generator = ToolsetGenerator(schema_dir=args.schema_dir, output_dir=args.output_dir)
        result = generator.generate_toolset(
            service=args.service,
            sdk=args.sdk,
            endpoint_limit=args.limit,
            dry_run=args.dry_run,
        )
        emit_result(result, args.format)
        return 0
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
