"""
Validate bundled endpoint schema files used by the skill.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def emit(message: str) -> None:
    """Write diagnostics to stderr."""
    print(message, file=sys.stderr)


def load_json_file(path: Path) -> dict[str, Any]:
    """Read JSON from mixed-encoding vendor files."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode JSON file: {path}")


def save_json_file(path: Path, payload: dict[str, Any]) -> None:
    """Write normalized JSON to disk."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class SchemaValidator:
    """Validate bundled endpoint schemas."""

    def __init__(self, schema_dir: str = "assets/endpoints", fix_paths: bool = False):
        self.schema_dir = Path(schema_dir)
        self.fix_paths = fix_paths

    def extract_endpoints(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract endpoint records from supported schema layouts."""
        if isinstance(data.get("endpoints"), list):
            return data["endpoints"]
        if isinstance(data.get("all_endpoints"), list):
            return data["all_endpoints"]
        endpoints_by_tag = data.get("endpoints_by_tag")
        if isinstance(endpoints_by_tag, dict):
            endpoints: list[dict[str, Any]] = []
            for tagged_endpoints in endpoints_by_tag.values():
                if isinstance(tagged_endpoints, list):
                    endpoints.extend(item for item in tagged_endpoints if isinstance(item, dict))
            return endpoints
        raise ValueError("JSON must contain 'endpoints', 'all_endpoints', or 'endpoints_by_tag'")

    def normalize_endpoint(self, endpoint: dict[str, Any], service_key: str) -> dict[str, Any]:
        """Normalize endpoint records before validation."""
        normalized = dict(endpoint)

        if not normalized.get("id"):
            operation_id = str(normalized.get("operation_id", "")).replace("/", "_").replace("-", "_")
            summary = str(normalized.get("summary", "")).strip().lower().replace(" ", "_")
            fallback = operation_id or summary or "endpoint"
            normalized["id"] = f"{service_key}_{fallback}".strip("_")

        if not normalized.get("description"):
            normalized["description"] = normalized.get("summary", normalized["id"])

        path_value = str(normalized.get("path", ""))
        if path_value and not path_value.startswith("/"):
            if self.fix_paths:
                normalized["path"] = f"/{path_value}"
            else:
                normalized["path"] = path_value

        return normalized

    def validate_endpoint(self, endpoint: dict[str, Any]) -> None:
        """Validate a single normalized endpoint."""
        missing_fields = [field for field in ("id", "method", "path", "description") if field not in endpoint]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        if endpoint["method"] not in VALID_METHODS:
            raise ValueError(f"Invalid HTTP method: {endpoint['method']}")

        if not str(endpoint["path"]).startswith("/"):
            raise ValueError(f"Path must start with /: {endpoint['path']}")

        if not endpoint["id"]:
            raise ValueError("Endpoint id cannot be empty")

    def validate_endpoints_file(self, filepath: Path) -> dict[str, Any]:
        """Validate one endpoint file and optionally persist path fixes."""
        payload = load_json_file(filepath)
        service_key = str(payload.get("service_key") or filepath.stem.replace("_endpoints", ""))
        endpoints = self.extract_endpoints(payload)
        errors: list[str] = []
        changed = False

        normalized_endpoints = []
        for index, endpoint in enumerate(endpoints):
            normalized = self.normalize_endpoint(endpoint, service_key)
            normalized_endpoints.append(normalized)
            if normalized != endpoint:
                changed = True
            try:
                self.validate_endpoint(normalized)
            except ValueError as exc:
                endpoint_id = endpoint.get("id") or endpoint.get("operation_id") or "unknown"
                errors.append(f"Endpoint {index} ({endpoint_id}): {exc}")

        if errors:
            return {"success": False, "file": str(filepath), "errors": errors, "changed": changed}

        if self.fix_paths and changed and isinstance(payload.get("all_endpoints"), list):
            payload["all_endpoints"] = normalized_endpoints
            save_json_file(filepath, payload)

        return {
            "success": True,
            "file": str(filepath),
            "endpoint_count": len(normalized_endpoints),
            "changed": changed,
        }

    def validate_all_schemas(self) -> dict[str, Any]:
        """Validate every bundled endpoint file in the schema directory."""
        schema_files = sorted(self.schema_dir.glob("*_endpoints.json"))
        if not schema_files:
            raise FileNotFoundError(f"No schema files found in {self.schema_dir}")

        results = [self.validate_endpoints_file(path) for path in schema_files]
        errors = [result for result in results if not result["success"]]

        return {
            "success": not errors,
            "schema_dir": str(self.schema_dir),
            "files_checked": len(results),
            "results": results,
        }


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI args."""
    parser = argparse.ArgumentParser(
        description="Validate bundled endpoint schema files used by the skill.",
        epilog=(
            "Examples:\n"
            "  python scripts/validate_schema.py\n"
            "  python scripts/validate_schema.py --schema-dir assets/endpoints --fix-paths"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--schema-dir",
        default="assets/endpoints",
        help="Directory containing bundled endpoint files",
    )
    parser.add_argument(
        "--fix-paths",
        action="store_true",
        help="Auto-prefix endpoint paths with '/' when safe to do so",
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
        print(f"validated {payload['files_checked']} schema file(s)")
        return

    failed = [item for item in payload["results"] if not item["success"]]
    print(f"validation failed for {len(failed)} schema file(s)")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        validator = SchemaValidator(schema_dir=args.schema_dir, fix_paths=args.fix_paths)
        result = validator.validate_all_schemas()
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
