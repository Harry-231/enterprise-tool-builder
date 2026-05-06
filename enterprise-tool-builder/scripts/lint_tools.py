"""
Lint and validate generated tools.

Checks for code quality, docstring completeness, type hints, and schema presence.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class ToolLinter:
    """Lint LangChain tools for quality."""

    def __init__(self, tools_dir: str = "generated_tools"):
        """Initialize linter."""
        self.tools_dir = Path(tools_dir)

    def lint_tool_file(self, filepath: Path) -> List[str]:
        """
        Lint a single tool file.

        Args:
            filepath: Path to tool Python file.

        Returns:
            List of linting issues found.
        """
        issues = []

        if not filepath.exists():
            return [f"File not found: {filepath}"]

        with open(filepath, "r") as f:
            content = f.read()

        # Check for docstring
        if '"""' not in content:
            issues.append("Missing module docstring")

        # Check for @tool decorator
        if "@tool" not in content:
            issues.append("Missing @tool decorator")

        # Check for function docstring
        if not re.search(r'def \w+\([^)]*\):\s+"""', content):
            issues.append("Tool function missing docstring")

        # Check for type hints
        if not re.search(r"def \w+\([^)]*:\s*\w+", content):
            issues.append("Function parameters missing type hints")

        # Check for return type hint
        if not re.search(r"\)\s*->\s*\w+:", content):
            issues.append("Function return type missing")

        # Check for Args section in docstring
        if 'Args:' not in content and '(' in content:
            issues.append("Docstring missing Args section")

        # Check for Returns section in docstring
        if 'Returns:' not in content:
            issues.append("Docstring missing Returns section")

        # Check for implementation (not just placeholder)
        if 'TODO' in content and content.count('TODO') > 2:
            issues.append("Too many TODO placeholders")

        return issues

    def lint_all_tools(self) -> Dict[str, List[str]]:
        """
        Lint all tool files in directory.

        Returns:
            Dictionary mapping filenames to issues found.
        """
        print(f"Linting tools in {self.tools_dir}...")

        results = {}
        tool_files = list(self.tools_dir.glob("**/*.py"))

        if not tool_files:
            print("No tool files found")
            return results

        for tool_file in tool_files:
            if tool_file.name != "__init__.py":
                issues = self.lint_tool_file(tool_file)
                if issues:
                    results[str(tool_file)] = issues

        return results

    def check_docstring_quality(self, filepath: Path) -> Dict:
        """
        Check docstring quality and completeness.

        Args:
            filepath: Path to tool file.

        Returns:
            Dictionary with quality metrics.
        """
        with open(filepath, "r") as f:
            content = f.read()

        metrics = {
            "has_module_docstring": '"""' in content,
            "has_function_docstring": "@tool" in content,
            "has_args_section": "Args:" in content,
            "has_returns_section": "Returns:" in content,
            "has_raises_section": "Raises:" in content,
            "has_examples": "Example:" in content,
            "docstring_length": len(
                re.search(r'"""(.*?)"""', content, re.DOTALL).group(1)
                if re.search(r'"""(.*?)"""', content, re.DOTALL)
                else ""
            ),
        }

        return metrics

    def generate_report(self, lint_results: Dict[str, List[str]]) -> str:
        """
        Generate a linting report.

        Args:
            lint_results: Results from lint_all_tools().

        Returns:
            Formatted report string.
        """
        report = "\nLinting Report\n" + "=" * 50 + "\n"

        if not lint_results:
            report += "All tools passed linting!\n"
            return report

        total_files = len(lint_results)
        total_issues = sum(len(issues) for issues in lint_results.values())

        report += f"Files with issues: {total_files}\n"
        report += f"Total issues found: {total_issues}\n\n"

        for filepath, issues in lint_results.items():
            report += f"\n{filepath}:\n"
            for issue in issues:
                report += f"  - {issue}\n"

        report += "\n" + "=" * 50 + "\n"
        return report

    def print_report(self, lint_results: Dict[str, List[str]]):
        """Print linting report to console."""
        report = self.generate_report(lint_results)
        print(report)


if __name__ == "__main__":
    linter = ToolLinter()
    results = linter.lint_all_tools()
    linter.print_report(results)

    # Exit with error code if issues found
    exit(1 if results else 0)
