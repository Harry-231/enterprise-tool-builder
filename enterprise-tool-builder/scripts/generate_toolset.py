"""
Batch generate all tools for a service from its endpoints schema.

Processes a service's endpoint JSON file and generates all corresponding tools.
"""

import json
from pathlib import Path
from typing import Optional
from generate_tool import ToolGenerator


class ToolsetGenerator:
    """Generate complete toolsets for services."""

    def __init__(
        self,
        schema_dir: str = "assets/endpoints",
        output_dir: str = "generated_tools",
    ):
        """Initialize toolset generator."""
        self.schema_dir = Path(schema_dir)
        self.output_dir = Path(output_dir)
        self.generator = ToolGenerator(output_dir)

    def generate_toolset_for_service(self, service: str) -> int:
        """
        Generate all tools for a service.

        Args:
            service: Service name (e.g., 'jira', 'slack', 'github').

        Returns:
            Number of tools generated.
        """
        schema_file = self.schema_dir / f"{service}_endpoints.json"

        if not schema_file.exists():
            print(f"Schema file not found: {schema_file}")
            return 0

        with open(schema_file, "r") as f:
            schema = json.load(f)

        service_key = schema.get("service_key", service)
        endpoints = self.generator.extract_endpoints(schema)
        print(f"\nGenerating {len(endpoints)} tools for {service}...")

        count = 0
        for endpoint in endpoints:
            try:
                endpoint = self.generator.normalize_endpoint(endpoint, service_key)
                tool_code = self.generator.generate_tool_from_endpoint(endpoint, service_key)
                filename = f"{endpoint['id']}.py"
                self.generator.save_tool(tool_code, filename)
                count += 1
            except Exception as e:
                endpoint_id = endpoint.get("id") or endpoint.get("operation_id") or "unknown"
                print(f"Error generating tool for {endpoint_id}: {e}")

        return count

    def generate_all_toolsets(self) -> int:
        """
        Generate toolsets for all services.

        Returns:
            Total number of tools generated.
        """
        print("Generating toolsets for all services...")

        schema_files = list(self.schema_dir.glob("*_endpoints.json"))

        if not schema_files:
            print("No schema files found")
            return 0

        total_tools = 0
        for schema_file in schema_files:
            # Extract service name from filename
            service = schema_file.stem.replace("_endpoints", "")
            try:
                count = self.generate_toolset_for_service(service)
                total_tools += count
            except Exception as e:
                print(f"Error processing {service}: {e}")

        print(f"\nTotal tools generated: {total_tools}")
        return total_tools


if __name__ == "__main__":
    generator = ToolsetGenerator()
    total = generator.generate_all_toolsets()
    exit(0 if total > 0 else 1)
