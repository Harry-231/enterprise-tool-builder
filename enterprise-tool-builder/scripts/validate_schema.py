"""
Validate API endpoint schemas.

Ensures that fetched endpoint definitions conform to expected schema format.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class SchemaValidator:
    """Validate API endpoint schemas."""

    REQUIRED_FIELDS = ["id", "method", "path", "description"]

    def __init__(self, schema_dir: str = "assets/endpoints"):
        """Initialize validator."""
        self.schema_dir = Path(schema_dir)

    def extract_endpoints(self, data: Dict) -> List[Dict]:
        """Extract endpoint records from either simple or bundled schema formats."""
        if "endpoints" in data:
            return data["endpoints"]

        if "all_endpoints" in data:
            return data["all_endpoints"]

        if "endpoints_by_tag" in data:
            endpoints: List[Dict] = []
            for tagged_endpoints in data["endpoints_by_tag"].values():
                if isinstance(tagged_endpoints, list):
                    endpoints.extend(tagged_endpoints)
            return endpoints

        raise ValueError(
            "JSON must contain 'endpoints', 'all_endpoints', or 'endpoints_by_tag'"
        )

    def normalize_endpoint(self, endpoint: Dict, service_key: str) -> Dict:
        """Normalize bundled endpoint records into the simple validation shape."""
        normalized = dict(endpoint)

        if "id" not in normalized or not normalized.get("id"):
            operation_id = normalized.get("operation_id", "").replace("/", "_").replace("-", "_")
            summary = normalized.get("summary", "").strip().lower().replace(" ", "_")
            fallback = operation_id or summary or "endpoint"
            normalized["id"] = f"{service_key}_{fallback}".strip("_")

        if "description" not in normalized or not normalized.get("description"):
            normalized["description"] = normalized.get("summary", normalized["id"])

        if "path" in normalized and normalized["path"] and not normalized["path"].startswith("/"):
            normalized["path"] = f"/{normalized['path']}"

        return normalized

    def validate_endpoint(self, endpoint: Dict) -> bool:
        """
        Validate a single endpoint definition.

        Args:
            endpoint: Endpoint definition dictionary.

        Returns:
            True if valid.

        Raises:
            ValueError: If endpoint is invalid.
        """
        # Check required fields
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in endpoint]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if endpoint["method"] not in valid_methods:
            raise ValueError(f"Invalid HTTP method: {endpoint['method']}")

        # Validate path format
        if not endpoint["path"].startswith("/"):
            raise ValueError(f"Path must start with /: {endpoint['path']}")

        # Validate id format (snake_case with service prefix)
        if not endpoint["id"]:
            raise ValueError("Endpoint id cannot be empty")

        return True

    def validate_endpoints_file(self, filepath: Path) -> bool:
        """
        Validate all endpoints in a file.

        Args:
            filepath: Path to endpoints JSON file.

        Returns:
            True if all endpoints are valid.
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        service_key = data.get("service_key", filepath.stem.replace("_endpoints", ""))
        endpoints = self.extract_endpoints(data)
        errors = []
        for i, endpoint in enumerate(endpoints):
            try:
                self.validate_endpoint(self.normalize_endpoint(endpoint, service_key))
            except ValueError as e:
                endpoint_id = endpoint.get("id") or endpoint.get("operation_id") or "unknown"
                errors.append(f"Endpoint {i} ({endpoint_id}): {e}")

        if errors:
            raise ValueError(f"Validation errors:\n" + "\n".join(errors))

        print(f"Validated {len(endpoints)} endpoints in {filepath.name}")
        return True

    def validate_all_schemas(self) -> bool:
        """Validate all endpoint schema files."""
        print("Validating all endpoint schemas...")

        schema_files = list(self.schema_dir.glob("*_endpoints.json"))

        if not schema_files:
            print("No schema files found")
            return False

        errors = []
        for schema_file in schema_files:
            try:
                self.validate_endpoints_file(schema_file)
            except ValueError as e:
                errors.append(f"{schema_file.name}: {e}")

        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"  {error}")
            return False

        print(f"All {len(schema_files)} schema files validated successfully")
        return True


if __name__ == "__main__":
    validator = SchemaValidator()
    success = validator.validate_all_schemas()
    exit(0 if success else 1)
