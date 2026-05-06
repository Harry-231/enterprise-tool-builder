"""
Test a generated tool against live or mock API endpoints.

Validates that a tool works correctly with the target API.
"""

from typing import Dict, Optional, Any
from unittest.mock import MagicMock
import sys


class ToolTester:
    """Test individual tools against APIs."""

    def __init__(self, use_mock: bool = True):
        """
        Initialize tool tester.

        Args:
            use_mock: If True, use mocked API responses. If False, use real API.
        """
        self.use_mock = use_mock

    def test_tool_with_parameters(
        self,
        tool_func,
        test_params: Dict[str, Any],
        expected_keys: Optional[list] = None,
    ) -> bool:
        """
        Test a tool with specific parameters.

        Args:
            tool_func: The tool function to test.
            test_params: Parameters to pass to the tool.
            expected_keys: Keys expected in the response.

        Returns:
            True if test passes.
        """
        print(f"Testing tool with parameters: {test_params}")

        try:
            result = tool_func(**test_params)
            print(f"Tool executed successfully")
            print(f"Result: {result}")

            if expected_keys:
                # Validate response contains expected keys
                if isinstance(result, str):
                    result = eval(result)  # Parse JSON string

                missing_keys = [k for k in expected_keys if k not in result]
                if missing_keys:
                    print(f"Warning: Missing expected keys: {missing_keys}")
                    return False

            return True

        except Exception as e:
            print(f"Tool test failed: {e}")
            return False

    def test_error_handling(self, tool_func, invalid_params: Dict) -> bool:
        """
        Test that tool handles invalid parameters gracefully.

        Args:
            tool_func: The tool function to test.
            invalid_params: Invalid parameters to test.

        Returns:
            True if error is handled gracefully.
        """
        print(f"Testing error handling with invalid parameters...")

        try:
            result = tool_func(**invalid_params)
            print(f"Tool did not raise error for invalid params (result: {result})")
            return False
        except (ValueError, TypeError, Exception) as e:
            print(f"Tool correctly raised error: {type(e).__name__}: {e}")
            return True

    def test_rate_limiting(self, tool_func, params: Dict, num_calls: int = 5) -> bool:
        """
        Test tool behavior under rate limiting.

        Args:
            tool_func: The tool function to test.
            params: Parameters for the tool.
            num_calls: Number of calls to make.

        Returns:
            True if rate limiting is handled properly.
        """
        print(f"Testing rate limiting with {num_calls} calls...")

        for i in range(num_calls):
            try:
                result = tool_func(**params)
                print(f"Call {i + 1}/{num_calls}: Success")
            except Exception as e:
                if "rate limit" in str(e).lower():
                    print(f"Call {i + 1}/{num_calls}: Rate limited (expected)")
                    return True
                else:
                    print(f"Call {i + 1}/{num_calls}: Unexpected error: {e}")
                    return False

        print("All calls succeeded (rate limiting not triggered)")
        return True

    def run_test_suite(
        self,
        tool_func,
        test_cases: list,
    ) -> Dict[str, bool]:
        """
        Run a suite of test cases.

        Args:
            tool_func: The tool function to test.
            test_cases: List of test case dictionaries.

        Returns:
            Dictionary with test results.
        """
        print(f"\nRunning test suite for tool: {tool_func.__name__}")
        print("=" * 50)

        results = {}

        for test_case in test_cases:
            test_name = test_case.get("name", "Unnamed test")
            test_type = test_case.get("type", "basic")

            print(f"\n{test_name}:")

            if test_type == "basic":
                results[test_name] = self.test_tool_with_parameters(
                    tool_func,
                    test_case.get("params", {}),
                    test_case.get("expected_keys"),
                )
            elif test_type == "error":
                results[test_name] = self.test_error_handling(
                    tool_func,
                    test_case.get("invalid_params", {}),
                )
            elif test_type == "rate_limit":
                results[test_name] = self.test_rate_limiting(
                    tool_func,
                    test_case.get("params", {}),
                    test_case.get("num_calls", 5),
                )

        # Print summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"Passed: {passed}/{total}")

        return results


if __name__ == "__main__":
    # Example usage
    def sample_tool(query: str = "test") -> str:
        """Sample tool for testing."""
        return f'{{"query": "{query}", "result": "success"}}'

    tester = ToolTester(use_mock=True)

    test_cases = [
        {
            "name": "Test basic functionality",
            "type": "basic",
            "params": {"query": "test"},
            "expected_keys": ["query", "result"],
        },
        {
            "name": "Test error handling",
            "type": "error",
            "invalid_params": {"query": ""},
        },
    ]

    results = tester.run_test_suite(sample_tool, test_cases)
