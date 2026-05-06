"""
Base LangChain @tool decorated function scaffold.

This template demonstrates the basic pattern for creating a simple LangChain tool.
"""

from langchain.tools import tool


@tool
def sample_api_call(query: str, limit: int = 10) -> str:
    """
    Call a sample enterprise API endpoint.

    Retrieve data from the API based on the query parameter.
    This tool serves as a template for simple tool implementations.

    Args:
        query: The search query or filter criteria for the API call.
        limit: Maximum number of results to return (default: 10).

    Returns:
        A formatted string containing the API response data.

    Example:
        >>> sample_api_call("customer search", limit=5)
        "Results: [...]"
    """
    # TODO: Implement actual API call logic here
    # 1. Build request URL with query parameters
    # 2. Add authentication headers
    # 3. Make HTTP request
    # 4. Parse and format response
    # 5. Handle errors gracefully

    api_response = f"Results for query: {query} (limit: {limit})"
    return api_response


if __name__ == "__main__":
    # Test the tool
    result = sample_api_call("test query", limit=5)
    print(result)
