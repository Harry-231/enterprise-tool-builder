"""
Summarize bundled enterprise endpoint JSON files.

Use this before generation to understand coverage, tags, and candidate actions.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def extract_endpoints(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return endpoints from supported schema layouts."""
    if isinstance(payload.get("endpoints"), list):
        return payload["endpoints"]

    if isinstance(payload.get("all_endpoints"), list):
        return payload["all_endpoints"]

    endpoints_by_tag = payload.get("endpoints_by_tag")
    if isinstance(endpoints_by_tag, dict):
        endpoints: list[dict[str, Any]] = []
        for tagged in endpoints_by_tag.values():
            if isinstance(tagged, list):
                endpoints.extend(item for item in tagged if isinstance(item, dict))
        return endpoints

    return []


def normalize_name(endpoint: dict[str, Any]) -> str:
    """Pick the most useful display name for an endpoint."""
    return (
        endpoint.get("id")
        or endpoint.get("operation_id")
        or endpoint.get("summary")
        or endpoint.get("path")
        or "unknown-endpoint"
    )


def iter_tags(endpoint: dict[str, Any]) -> Iterable[str]:
    """Yield normalized tags for an endpoint."""
    tags = endpoint.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                yield tag.strip()


def build_summary(payload: dict[str, Any], path: Path, limit: int) -> str:
    """Render a compact summary for terminal use."""
    endpoints = extract_endpoints(payload)
    methods = Counter()
    tags = Counter()

    for endpoint in endpoints:
        method = endpoint.get("method")
        if isinstance(method, str) and method:
            methods[method.upper()] += 1
        for tag in iter_tags(endpoint):
            tags[tag] += 1

    lines = [
        f"File: {path}",
        f"Service: {payload.get('service', 'unknown')}",
        f"Service key: {payload.get('service_key', 'unknown')}",
        f"Base URL: {payload.get('base_url', 'unknown')}",
        f"Endpoints discovered: {len(endpoints)}",
    ]

    if methods:
        method_bits = ", ".join(f"{name}={count}" for name, count in sorted(methods.items()))
        lines.append(f"Methods: {method_bits}")

    if tags:
        top_tags = ", ".join(f"{name}={count}" for name, count in tags.most_common(8))
        lines.append(f"Top tags: {top_tags}")

    lines.append("Candidate endpoints:")
    for endpoint in endpoints[:limit]:
        lines.append(
            f"- {endpoint.get('method', '?')} {endpoint.get('path', '?')} :: {normalize_name(endpoint)}"
        )

    if len(endpoints) > limit:
        lines.append(f"... {len(endpoints) - limit} more endpoints not shown")

    return "\n".join(lines)


def build_summary_payload(payload: dict[str, Any], path: Path, limit: int, offset: int) -> dict[str, Any]:
    """Return a structured summary payload."""
    endpoints = extract_endpoints(payload)
    methods = Counter()
    tags = Counter()

    for endpoint in endpoints:
        method = endpoint.get("method")
        if isinstance(method, str) and method:
            methods[method.upper()] += 1
        for tag in iter_tags(endpoint):
            tags[tag] += 1

    slice_end = offset + limit
    return {
        "file": str(path),
        "service": payload.get("service", "unknown"),
        "service_key": payload.get("service_key", "unknown"),
        "base_url": payload.get("base_url", "unknown"),
        "endpoints_discovered": len(endpoints),
        "methods": dict(sorted(methods.items())),
        "top_tags": dict(tags.most_common(8)),
        "offset": offset,
        "limit": limit,
        "has_more": slice_end < len(endpoints),
        "candidates": [
            {
                "method": endpoint.get("method", "?"),
                "path": endpoint.get("path", "?"),
                "name": normalize_name(endpoint),
            }
            for endpoint in endpoints[offset:slice_end]
        ],
    }


def load_json_file(path: Path) -> dict[str, Any]:
    """Load JSON while tolerating the mixed encodings common in vendor dumps."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Unable to decode {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize enterprise endpoint JSON files.")
    parser.add_argument("schema_file", help="Path to a bundled endpoint JSON file")
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum number of candidate endpoints to show",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Start listing candidates from this offset",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema_file)
    if not schema_path.exists():
        raise SystemExit(f"Schema file not found: {schema_path}")

    payload = load_json_file(schema_path)
    if args.format == "json":
        print(json.dumps(build_summary_payload(payload, schema_path, args.limit, args.offset), indent=2))
    else:
        print(build_summary(payload, schema_path, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
