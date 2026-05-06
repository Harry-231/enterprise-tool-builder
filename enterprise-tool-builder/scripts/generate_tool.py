"""
Generate LangChain tool drafts from enterprise endpoint definitions.

Supports Python, TypeScript, and JavaScript targets so the skill can build
tools in the user's preferred LangChain SDK.
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
import sys
from pathlib import Path
from typing import Any


SDK_PYTHON = "python"
SDK_TYPESCRIPT = "typescript"
SDK_JAVASCRIPT = "javascript"
SUPPORTED_SDKS = (SDK_PYTHON, SDK_TYPESCRIPT, SDK_JAVASCRIPT)


def emit(message: str) -> None:
    """Write diagnostics to stderr."""
    print(message, file=sys.stderr)


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Render structured or text output."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return

    if "path" in payload:
        print(f"generated {payload['sdk']} tool: {payload['path']}")
        return

    print(payload.get("message", "completed"))


def load_json_file(path: Path) -> dict[str, Any]:
    """Load JSON from mixed-encoding vendor files."""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode JSON file: {path}")


def extract_endpoints(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract endpoint records from supported schema shapes."""
    if isinstance(schema.get("endpoints"), list):
        return schema["endpoints"]

    if isinstance(schema.get("all_endpoints"), list):
        return schema["all_endpoints"]

    endpoints_by_tag = schema.get("endpoints_by_tag")
    if isinstance(endpoints_by_tag, dict):
        endpoints: list[dict[str, Any]] = []
        for tagged_endpoints in endpoints_by_tag.values():
            if isinstance(tagged_endpoints, list):
                endpoints.extend(item for item in tagged_endpoints if isinstance(item, dict))
        return endpoints

    return []


def slugify(value: str, fallback: str = "endpoint") -> str:
    """Convert arbitrary text into a stable snake_case identifier."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return normalized or fallback


def python_identifier(value: str, fallback: str = "param") -> str:
    """Return a safe Python identifier."""
    normalized = slugify(value, fallback=fallback)
    if normalized[0].isdigit():
        normalized = f"{fallback}_{normalized}"
    if keyword.iskeyword(normalized):
        normalized = f"{normalized}_value"
    return normalized


def js_identifier(value: str, fallback: str = "param") -> str:
    """Return a safe JavaScript identifier."""
    normalized = slugify(value, fallback=fallback)
    if normalized[0].isdigit():
        normalized = f"{fallback}_{normalized}"
    return normalized


def to_pascal_case(value: str) -> str:
    """Convert a snake-ish identifier to PascalCase."""
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    collapsed = "".join(part[:1].upper() + part[1:] for part in parts if part)
    return collapsed or "ToolInput"


def normalize_endpoint(endpoint: dict[str, Any], service_key: str) -> dict[str, Any]:
    """Normalize bundled endpoint records into a consistent shape."""
    normalized = dict(endpoint)

    if not normalized.get("id"):
        operation_id = str(normalized.get("operation_id", ""))
        summary = str(normalized.get("summary", ""))
        candidate = slugify(operation_id or summary or normalized.get("path", "endpoint"))
        normalized["id"] = f"{service_key}_{candidate}".strip("_")

    if not normalized.get("description"):
        normalized["description"] = normalized.get("summary") or normalized["id"]

    if not normalized.get("method"):
        normalized["method"] = "GET"

    path_value = str(normalized.get("path", ""))
    if path_value and not path_value.startswith("/"):
        normalized["path"] = f"/{path_value}"

    return normalized


def infer_schema_name(endpoint_id: str) -> str:
    """Pick a stable args schema class/interface name."""
    return f"{to_pascal_case(endpoint_id)}Input"


def endpoint_parameters(endpoint: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten endpoint parameters into a list."""
    params = endpoint.get("parameters")
    if isinstance(params, list):
        flattened = []
        for param in params:
            if isinstance(param, dict):
                flattened.append(param)
        return flattened

    if isinstance(params, dict):
        flattened = []
        for location, values in params.items():
            if isinstance(values, dict):
                for name, description in values.items():
                    flattened.append(
                        {
                            "name": name,
                            "in": location,
                            "required": location == "path",
                            "description": description,
                        }
                    )
        return flattened

    return []


def normalize_parameters(endpoint: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize parameters into a predictable structure."""
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, param in enumerate(endpoint_parameters(endpoint), start=1):
        raw_name = str(param.get("name") or f"param_{index}")
        location = str(param.get("in") or "query")
        required = bool(param.get("required", location == "path"))
        description = str(param.get("description") or f"{location} parameter `{raw_name}`.")
        normalized_name = raw_name if raw_name.strip() else f"param_{index}"
        key = f"{location}:{normalized_name}"
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "name": normalized_name,
                "location": location,
                "required": required,
                "description": description.strip(),
            }
        )

    return normalized


def python_parameter_docs(parameters: list[dict[str, Any]]) -> str:
    """Build a Python docstring Args block."""
    if not parameters:
        return "    Args:\n        query: Search or lookup text for the endpoint.\n"

    lines = ["    Args:"]
    for param in parameters:
        lines.append(
            f"        {python_identifier(param['name'])}: {param['description']} "
            f"(source: {param['location']})."
        )
    return "\n".join(lines) + "\n"


def python_args_schema(endpoint: dict[str, Any], parameters: list[dict[str, Any]]) -> tuple[str, str]:
    """Create a Pydantic schema class and function signature."""
    schema_name = infer_schema_name(endpoint["id"])
    field_lines: list[str] = []
    signature_parts: list[str] = []

    if not parameters:
        field_lines.append(
            '    query: str = Field(..., description="Search or lookup text for the endpoint.", min_length=1)'
        )
        signature_parts.append("query: str")
    else:
        for param in parameters:
            identifier = python_identifier(param["name"])
            field_expr = (
                f'Field(..., description="{param["description"]} (source: {param["location"]}).")'
                if param["required"]
                else f'Field(default=None, description="{param["description"]} (source: {param["location"]}).")'
            )
            annotation = "str" if param["required"] else "str | None"
            field_lines.append(f"    {identifier}: {annotation} = {field_expr}")
            signature_parts.append(f"{identifier}: {annotation}" if param["required"] else f"{identifier}: {annotation} = None")

    schema_block = "\n".join(
        [
            f"class {schema_name}(BaseModel):",
            f'    """Input schema for `{endpoint["id"]}`."""',
            "",
            *field_lines,
            "",
        ]
    )

    return schema_block, ", ".join(signature_parts)


def python_response_body(endpoint: dict[str, Any], parameters: list[dict[str, Any]]) -> str:
    """Create the Python return payload expression."""
    items = [
        '        "success": True,',
        '        "data": {',
        f'            "operation": "{endpoint["id"]}",',
        f'            "method": "{endpoint["method"]}",',
        f'            "path": "{endpoint["path"]}",',
        "            \"request\": {",
    ]
    if parameters:
        for param in parameters:
            identifier = python_identifier(param["name"])
            items.append(f'                "{identifier}": {identifier},')
    else:
        items.append("                \"query\": query,")
    items.extend(
        [
            "            },",
            "        },",
            '        "error": None,',
            '        "metadata": {"draft": True},',
            "    }",
        ]
    )
    return "\n".join(items)


def generate_python_tool(endpoint: dict[str, Any]) -> str:
    """Generate a Python LangChain tool draft."""
    parameters = normalize_parameters(endpoint)
    schema_block, signature = python_args_schema(endpoint, parameters)
    param_docs = python_parameter_docs(parameters)
    tool_name = python_identifier(endpoint["id"], fallback="tool")

    return "\n".join(
        [
            '"""',
            f'{endpoint["description"]}',
            "",
            "Generated draft for LangChain Python tools.",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "import json",
            "from pydantic import BaseModel, Field",
            "from langchain.tools import tool",
            "",
            schema_block,
            f"@tool(args_schema={infer_schema_name(endpoint['id'])})",
            f"def {tool_name}({signature}) -> str:",
            '    """',
            f"    {endpoint['description']}",
            "",
            param_docs.rstrip(),
            "",
            "    Returns:",
            "        JSON string with the standard success/data/error/metadata envelope.",
            '    """',
            "    # TODO: Replace this draft with a real API request.",
            "    payload = {",
            python_response_body(endpoint, parameters),
            "    return json.dumps(payload)",
            "",
        ]
    )


def zod_schema_lines(endpoint: dict[str, Any], include_types: bool) -> tuple[str, list[dict[str, Any]]]:
    """Create a Zod schema block and return normalized params."""
    parameters = normalize_parameters(endpoint)
    lines = ["const schema = z.object({"]

    if not parameters:
        lines.append(
            '  query: z.string().min(1).describe("Search or lookup text for the endpoint."),'
        )
    else:
        for param in parameters:
            identifier = js_identifier(param["name"])
            base = f'z.string().describe("{param["description"]} (source: {param["location"]}).")'
            if not param["required"]:
                base += ".optional()"
            lines.append(f"  {identifier}: {base},")

    lines.append("});")
    if include_types:
        lines.append("")
        lines.append("type ToolInput = z.infer<typeof schema>;")
    return "\n".join(lines), parameters


def js_payload_lines(endpoint: dict[str, Any], parameters: list[dict[str, Any]]) -> str:
    """Build the JS/TS payload object."""
    request_lines = []
    if parameters:
        for param in parameters:
            identifier = js_identifier(param["name"])
            request_lines.append(f"        {identifier},")
    else:
        request_lines.append("        query,")

    return "\n".join(
        [
            "  return {",
            "    success: true,",
            "    data: {",
            f'      operation: "{endpoint["id"]}",',
            f'      method: "{endpoint["method"]}",',
            f'      path: "{endpoint["path"]}",',
            "      request: {",
            *request_lines,
            "      },",
            "    },",
            "    error: null,",
            "    metadata: { draft: true },",
            "  };",
        ]
    )


def generate_jsts_tool(endpoint: dict[str, Any], sdk: str) -> str:
    """Generate a TypeScript or JavaScript LangChain tool draft."""
    include_types = sdk == SDK_TYPESCRIPT
    schema_block, parameters = zod_schema_lines(endpoint, include_types=include_types)
    identifier = js_identifier(endpoint["id"], fallback="tool")

    tool_callback_signature = "async (input: ToolInput)" if include_types else "async (input)"
    destructuring_line = (
        "  const { query } = input;"
        if not parameters
        else "  const { " + ", ".join(js_identifier(param["name"]) for param in parameters) + " } = input;"
    )

    lines = [
        "/**",
        f" * {endpoint['description']}",
        " *",
        f" * Generated draft for LangChain {sdk} tools.",
        " */",
        "",
        'import * as z from "zod";',
        'import { tool } from "langchain";',
        "",
        schema_block,
        "",
        f"export const {identifier} = tool(",
        f"  {tool_callback_signature} => {{",
        f"    {destructuring_line}",
        "    // TODO: Replace this draft with a real API request.",
        js_payload_lines(endpoint, parameters),
        "  },",
        "  {",
        f'    name: "{endpoint["id"]}",',
        f'    description: "{endpoint["description"]}",',
        "    schema,",
        "  }",
        ");",
        "",
    ]
    return "\n".join(lines)


class ToolGenerator:
    """Generate LangChain tool files from endpoint definitions."""

    def __init__(self, output_dir: str = "generated_tools"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_tool_code(self, endpoint: dict[str, Any], sdk: str) -> str:
        """Generate tool code for a target SDK."""
        if sdk == SDK_PYTHON:
            return generate_python_tool(endpoint)
        if sdk in (SDK_TYPESCRIPT, SDK_JAVASCRIPT):
            return generate_jsts_tool(endpoint, sdk=sdk)
        raise ValueError(f"Unsupported SDK: {sdk}")

    def save_tool(self, tool_code: str, filename: str) -> Path:
        """Write generated code to disk."""
        output_file = self.output_dir / filename
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(tool_code, encoding="utf-8")
        return output_file

    def generate_from_schema(
        self,
        schema_file: Path,
        service: str | None,
        endpoint_id: str | None,
        sdk: str,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Generate one tool from a schema file."""
        schema = load_json_file(schema_file)
        service_key = service or schema.get("service_key") or schema.get("service") or "service"

        matches = []
        for endpoint in extract_endpoints(schema):
            normalized = normalize_endpoint(endpoint, str(service_key))
            if endpoint_id and normalized["id"] != endpoint_id:
                continue
            matches.append(normalized)

        if not matches:
            raise ValueError("No matching endpoint found in schema")
        if len(matches) > 1 and endpoint_id is None:
            raise ValueError("Schema contains multiple endpoints; pass --endpoint-id to choose one")

        endpoint = matches[0]
        tool_code = self.generate_tool_code(endpoint, sdk=sdk)
        extension = {SDK_PYTHON: ".py", SDK_TYPESCRIPT: ".ts", SDK_JAVASCRIPT: ".js"}[sdk]
        filename = f"{endpoint['id']}{extension}"

        if dry_run:
            return {
                "success": True,
                "sdk": sdk,
                "endpoint_id": endpoint["id"],
                "filename": filename,
                "preview": tool_code[:1200],
                "dry_run": True,
            }

        output_path = self.save_tool(tool_code, filename)
        return {
            "success": True,
            "sdk": sdk,
            "endpoint_id": endpoint["id"],
            "filename": filename,
            "path": str(output_path),
            "dry_run": False,
        }


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Generate one LangChain tool draft from an endpoint schema.",
        epilog=(
            "Examples:\n"
            "  python scripts/generate_tool.py assets/endpoints/github_api_endpoints.json "
            "--endpoint-id github_agent_tasks_create_task_in_repo --sdk python\n"
            "  python scripts/generate_tool.py assets/endpoints/github_api_endpoints.json "
            "--endpoint-id github_agent_tasks_create_task_in_repo --sdk typescript --dry-run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("schema_file", help="Path to the endpoint JSON file")
    parser.add_argument("--service", help="Override the service key used for normalization")
    parser.add_argument("--endpoint-id", help="Generate a tool for one explicit endpoint id")
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
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the generated file metadata without writing it",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        generator = ToolGenerator(output_dir=args.output_dir)
        result = generator.generate_from_schema(
            schema_file=Path(args.schema_file),
            service=args.service,
            endpoint_id=args.endpoint_id,
            sdk=args.sdk,
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
