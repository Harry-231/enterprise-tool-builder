"""
StructuredTool with input schema pattern.

This template demonstrates how to create a LangChain tool with explicit
input validation using Pydantic BaseModel.
"""

from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool


class ToolInput(BaseModel):
    """Input schema for the structured tool."""

    query: str = Field(
        ...,
        description="The search query or filter criteria for the API call",
        min_length=1,
        max_length=500,
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return",
        ge=1,
        le=100,
    )
    filters: Optional[dict] = Field(
        default=None,
        description="Additional filter parameters as a dictionary",
    )


@tool(args_schema=ToolInput)
def structured_api_call(query: str, limit: int = 10, filters: Optional[dict] = None) -> str:
    """
    Call an enterprise API endpoint with structured input validation.

    This tool validates all inputs against the ToolInput schema before processing.
    Invalid inputs are rejected with clear error messages.

    Args:
        query: The search query or filter criteria (1-500 characters).
        limit: Maximum results to return (1-100, default: 10).
        filters: Optional dictionary of additional filter parameters.

    Returns:
        A formatted string containing the API response data.

    Raises:
        ValueError: If input validation fails.
        ConnectionError: If the API call fails.

    Example:
        >>> structured_api_call("customer", limit=5, filters={"status": "active"})
        "Results: [...]"
    """
    # TODO: Implement API call logic with validated inputs
    # 1. Inputs are already validated by Pydantic schema
    # 2. Build request with validated parameters
    # 3. Apply filters if provided
    # 4. Make API request
    # 5. Return formatted results

    filters_str = f", filters: {filters}" if filters else ""
    api_response = f"Results for query: {query} (limit: {limit}){filters_str}"
    return api_response


if __name__ == "__main__":
    # Test the structured tool
    result = structured_api_call("test", limit=5, filters={"status": "active"})
    print(result)
