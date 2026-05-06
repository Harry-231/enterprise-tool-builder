"""
Smoke-test a generated LangChain tool file.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import types
import sys
from pathlib import Path
from typing import Any


def emit(message: str) -> None:
    """Write diagnostics to stderr."""
    print(message, file=sys.stderr)


def parse_key_value(values: list[str] | None) -> dict[str, Any]:
    """Parse repeated key=value arguments."""
    parsed: dict[str, Any] = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"Expected key=value argument, received: {item}")
        key, value = item.split("=", 1)
        parsed[key] = value
    return parsed


def load_module(tool_file: Path):
    """Load a Python module from a file path."""
    ensure_runtime_stubs()
    spec = importlib.util.spec_from_file_location(tool_file.stem, tool_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Unable to import tool file: {tool_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_runtime_stubs() -> None:
    """Provide minimal runtime stubs when optional deps are unavailable."""
    if "langchain.tools" not in sys.modules:
        langchain_module = sys.modules.setdefault("langchain", types.ModuleType("langchain"))
        tools_module = types.ModuleType("langchain.tools")

        def tool_decorator(*decorator_args, **decorator_kwargs):
            if decorator_args and callable(decorator_args[0]) and not decorator_kwargs:
                return decorator_args[0]

            def wrap(func):
                return func

            return wrap

        tools_module.tool = tool_decorator
        sys.modules["langchain.tools"] = tools_module
        setattr(langchain_module, "tools", tools_module)


def normalize_result(result: Any) -> Any:
    """Decode JSON strings when possible."""
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result


def invoke_tool(tool_obj: Any, params: dict[str, Any]) -> Any:
    """Invoke a plain function or LangChain tool object."""
    if hasattr(tool_obj, "invoke"):
        return tool_obj.invoke(params)
    if callable(tool_obj):
        return tool_obj(**params)
    raise ValueError("Target object is not callable and does not implement invoke()")


def run_smoke_test(
    tool_file: Path,
    tool_name: str,
    params: dict[str, Any],
    expected_keys: list[str],
    invalid_params: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run success and optional failure-path checks."""
    module = load_module(tool_file)
    if not hasattr(module, tool_name):
        raise ValueError(f"Tool `{tool_name}` not found in {tool_file}")

    tool_obj = getattr(module, tool_name)
    result = normalize_result(invoke_tool(tool_obj, params))
    passed = True
    missing_keys: list[str] = []

    if expected_keys:
        if not isinstance(result, dict):
            passed = False
            missing_keys = expected_keys
        else:
            missing_keys = [key for key in expected_keys if key not in result]
            passed = not missing_keys

    invalid_result: dict[str, Any] | None = None
    if invalid_params is not None:
        try:
            invoke_tool(tool_obj, invalid_params)
            invalid_result = {"passed": False, "error": "tool accepted invalid params"}
            passed = False
        except Exception as exc:  # Expected path for failure testing
            invalid_result = {"passed": True, "error_type": type(exc).__name__, "message": str(exc)}

    return {
        "success": passed,
        "tool_file": str(tool_file),
        "tool_name": tool_name,
        "result": result,
        "missing_keys": missing_keys,
        "invalid_case": invalid_result,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build CLI args."""
    parser = argparse.ArgumentParser(
        description="Smoke-test a generated Python LangChain tool.",
        epilog=(
            "Examples:\n"
            "  python scripts/test_tool.py generated_tools/github_search.py --tool-name github_search "
            "--param query=langchain --expect-key success --expect-key data\n"
            "  python scripts/test_tool.py generated_tools/github_search.py --tool-name github_search "
            "--param query=langchain --invalid-param query="
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tool_file", help="Path to the generated Python tool file")
    parser.add_argument("--tool-name", required=True, help="Tool symbol name inside the module")
    parser.add_argument("--param", action="append", help="Valid key=value parameter", default=[])
    parser.add_argument("--invalid-param", action="append", help="Invalid key=value parameter", default=[])
    parser.add_argument("--expect-key", action="append", help="Key expected in a dict/JSON response", default=[])
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for script results",
    )
    return parser


def emit_result(payload: dict[str, Any], output_format: str) -> None:
    """Render test results."""
    if output_format == "json":
        print(json.dumps(payload, indent=2))
        return
    print("smoke test passed" if payload["success"] else "smoke test failed")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        params = parse_key_value(args.param)
        invalid_params = parse_key_value(args.invalid_param) if args.invalid_param else None
        result = run_smoke_test(
            tool_file=Path(args.tool_file),
            tool_name=args.tool_name,
            params=params,
            expected_keys=args.expect_key,
            invalid_params=invalid_params,
        )
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
