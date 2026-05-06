"""
Generate LangChain tools from API endpoint definitions.

Takes an endpoint JSON definition and generates a complete LangChain tool.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ToolGenerator:
    """Generate LangChain tools from endpoint definitions."""

    TEMPLATE_BASIC = '''"""
{description}
"""

from langchain.tools import tool


@tool
def {tool_name}({parameters}) -> str:
    """
    {description}

    {param_docs}

    Returns:
        API response as JSON string.
    """
    # TODO: Implement API call logic
    # 1. Build request URL and parameters
    # 2. Add authentication headers
    # 3. Make HTTP {method} request to {path}
    # 4. Handle errors gracefully
    # 5. Return formatted response

    return "Tool implementation pending"


if __name__ == "__main__":
    result = {tool_name}()
    print(result)
'''

    def __init__(self, output_dir: str = "generated_tools"):
        """Initialize generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_endpoints(self, schema: Dict) -> List[Dict]:
        """Extract endpoint records from either simple or bundled schema formats."""
        if "endpoints" in schema:
            return schema["endpoints"]

        if "all_endpoints" in schema:
            return schema["all_endpoints"]

        if "endpoints_by_tag" in schema:
            endpoints: List[Dict] = []
            for tagged_endpoints in schema["endpoints_by_tag"].values():
                if isinstance(tagged_endpoints, list):
                    endpoints.extend(tagged_endpoints)
            return endpoints

        return []

    def normalize_endpoint(self, endpoint: Dict, service: str) -> Dict:
        """Normalize bundled endpoint records into the simple generation shape."""
        normalized = dict(endpoint)

        if "id" not in normalized or not normalized.get("id"):
            operation_id = normalized.get("operation_id", "").replace("/", "_").replace("-", "_")
            summary = normalized.get("summary", "").strip().lower().replace(" ", "_")
            fallback = operation_id or summary or "endpoint"
            normalized["id"] = f"{service}_{fallback}".strip("_")

        if "description" not in normalized or not normalized.get("description"):
            normalized["description"] = normalized.get("summary", normalized["id"])

        if "path" in normalized and normalized["path"] and not normalized["path"].startswith("/"):
            normalized["path"] = f"/{normalized['path']}"

        return normalized

    def generate_tool_from_endpoint(self, endpoint: Dict, service: str) -> str:
        """
        Generate tool code from endpoint definition.

        Args:
            endpoint: Endpoint definition from API schema.
            service: Service name (e.g., 'jira', 'slack').

        Returns:
            Generated tool code as string.
        """
        endpoint = self.normalize_endpoint(endpoint, service)
        tool_name = endpoint["id"]
        description = endpoint["description"]
        method = endpoint["method"]
        path = endpoint["path"]

        # Generate parameter documentation
        param_docs = self._generate_param_docs(endpoint)

        # Generate parameter list (simplified for demo)
        parameters = "query: str = 'default'"

        # Generate tool code
        tool_code = self.TEMPLATE_BASIC.format(
            description=description,
            tool_name=tool_name,
            method=method,
            path=path,
            parameters=parameters,
            param_docs=param_docs,
        )

        return tool_code

    def _generate_param_docs(self, endpoint: Dict) -> str:
        """Generate parameter documentation."""
        if "parameters" not in endpoint:
            return "    Args:\n        query: Query parameter."

        if isinstance(endpoint["parameters"], list):
            docs = "    Args:\n"
            has_parameters = False
            for param in endpoint["parameters"]:
                name = param.get("name") or "query"
                description = param.get("description") or "Parameter."
                docs += f"        {name}: {description}\n"
                has_parameters = True
            return docs if has_parameters else "    Args:\n        query: Query parameter."

        docs = "    Args:\n"
        params = endpoint.get("parameters", {})

        for param_type in ["path", "query"]:
            if param_type in params:
                for param_name, param_info in params[param_type].items():
                    docs += f"        {param_name}: {param_info}\n"

        return docs

    def save_tool(self, tool_code: str, filename: str):
        """
        Save generated tool code to file.

        Args:
            tool_code: Generated tool code.
            filename: Output filename.
        """
        output_file = self.output_dir / filename
        with open(output_file, "w") as f:
            f.write(tool_code)
        print(f"Generated tool: {output_file}")

    def generate_tools_from_schema(
        self, schema_file: Path, service: str
    ):
        """
        Generate tools from all endpoints in a schema file.

        Args:
            schema_file: Path to endpoint schema JSON file.
            service: Service name.
        """
        with open(schema_file, "r") as f:
            schema = json.load(f)

        for endpoint in self.extract_endpoints(schema):
            endpoint = self.normalize_endpoint(endpoint, service)
            tool_code = self.generate_tool_from_endpoint(endpoint, service)
            filename = f"{endpoint['id']}.py"
            self.save_tool(tool_code, filename)


if __name__ == "__main__":
    # Example usage
    generator = ToolGenerator()

    # Generate a sample tool
    sample_endpoint = {
        "id": "sample_get_data",
        "method": "GET",
        "path": "/data",
        "description": "Retrieve data from the API",
        "parameters": {
            "query": {
                "id": "Data ID",
            }
        },
    }

    tool_code = generator.generate_tool_from_endpoint(sample_endpoint, "sample")
    generator.save_tool(tool_code, "sample_tool.py")
