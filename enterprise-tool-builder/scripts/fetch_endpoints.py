"""
Create bundled endpoint JSON from an OpenAPI document.

The source can be a local file or an HTTPS URL.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any


def emit(message: str) -> None:
    """Write diagnostics to stderr."""
    print(message, file=sys.stderr)


def load_json_source(source: str) -> dict[str, Any]:
    """Load JSON from a local path or URL."""
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            data = response.read()
        return json.loads(data.decode("utf-8"))

    path = Path(source)
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode JSON source: {source}")


def slugify(value: str, fallback: str = "endpoint") -> str:
    """Create a stable snake-ish identifier."""
    cleaned = "".join(char if char.isalnum() else "_" for char in value).strip("_").lower()
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned or fallback


def build_endpoint_record(path: str, method: str, operation: dict[str, Any], service_key: str) -> dict[str, Any]:
    """Convert one OpenAPI operation into the skill's endpoint schema."""
    operation_id = str(operation.get("operationId") or "")
    summary = str(operation.get("summary") or operation.get("description") or f"{method} {path}")
    endpoint_id = slugify(operation_id or summary)

    parameters = []
    for param in operation.get("parameters", []):
        if isinstance(param, dict):
            parameters.append(
                {
                    "name": param.get("name", ""),
                    "in": param.get("in", "query"),
                    "required": bool(param.get("required", False)),
                    "description": param.get("description", ""),
                }
            )

    return {
        "id": f"{service_key}_{endpoint_id}",
        "method": method.upper(),
        "path": path if path.startswith("/") else f"/{path}",
        "operation_id": operation_id or None,
        "summary": summary,
        "description": str(operation.get("description") or summary),
        "tags": operation.get("tags", []),
        "deprecated": bool(operation.get("deprecated", False)),
        "parameters": parameters,
    }


def extract_openapi_operations(spec: dict[str, Any], service_key: str, tag_filter: str | None) -> list[dict[str, Any]]:
    """Extract endpoint records from an OpenAPI paths object."""
    operations: list[dict[str, Any]] = []

    for path, methods in spec.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            if tag_filter and tag_filter not in operation.get("tags", []):
                continue
            operations.append(build_endpoint_record(path, method, operation, service_key))

    return operations


def build_bundle(
    spec: dict[str, Any],
    service: str,
    service_key: str,
    base_url: str,
    tag_filter: str | None,
    limit: int | None,
) -> dict[str, Any]:
    """Build the bundled endpoint JSON shape used by this skill."""
    operations = extract_openapi_operations(spec, service_key=service_key, tag_filter=tag_filter)
    if limit is not None:
        operations = operations[:limit]

    endpoints_by_tag: dict[str, list[dict[str, Any]]] = {}
    for operation in operations:
        tags = operation.get("tags") or ["untagged"]
        for tag in tags:
            endpoints_by_tag.setdefault(str(tag), []).append(operation)

    return {
        "service": service,
        "service_key": service_key,
        "base_url": base_url,
        "total_endpoints": len(operations),
        "endpoints_by_tag": endpoints_by_tag,
        "all_endpoints": operations,
    }


def write_bundle(bundle: dict[str, Any], output_path: Path, dry_run: bool) -> None:
    """Write the endpoint bundle unless dry-run is enabled."""
    if dry_run:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert an OpenAPI JSON source into a bundled enterprise endpoint file.",
        epilog=(
            "Examples:\n"
            "  python scripts/fetch_endpoints.py https://api.github.com/openapi.json "
            "--service github --service-key github --base-url https://api.github.com "
            "--output assets/endpoints/github_api_endpoints.json\n"
            "  python scripts/fetch_endpoints.py local-openapi.json --service slack --service-key slack --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", help="OpenAPI JSON file path or HTTPS URL")
    parser.add_argument("--service", required=True, help="Human-readable service name")
    parser.add_argument("--service-key", required=True, help="Stable service key used in endpoint ids")
    parser.add_argument("--base-url", required=True, help="Service base URL")
    parser.add_argument("--tag", help="Optional tag filter")
    parser.add_argument("--limit", type=int, help="Maximum operations to include")
    parser.add_argument(
        "--output",
        default="assets/endpoints/generated_endpoints.json",
        help="Output path for the bundled endpoint JSON file",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing the bundle file")
    return parser


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Render structured or concise text output."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return
    print(f"prepared {payload['total_endpoints']} endpoints for {payload['service_key']}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        spec = load_json_source(args.source)
        bundle = build_bundle(
            spec=spec,
            service=args.service,
            service_key=args.service_key,
            base_url=args.base_url,
            tag_filter=args.tag,
            limit=args.limit,
        )
        output_path = Path(args.output)
        write_bundle(bundle, output_path=output_path, dry_run=args.dry_run)
        emit_result(
            {
                "success": True,
                "service": args.service,
                "service_key": args.service_key,
                "output": str(output_path),
                "dry_run": args.dry_run,
                "total_endpoints": bundle["total_endpoints"],
            },
            args.format,
        )
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
