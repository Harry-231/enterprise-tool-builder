"""
Template for paginated list endpoints.

This template demonstrates how to handle API endpoints that return
paginated results, with support for offset-based and cursor-based pagination.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain.tools import tool


class PaginationInput(BaseModel):
    """Input schema with pagination support."""

    query: str = Field(..., description="Search query")
    page: int = Field(default=1, description="Page number (1-based)", ge=1)
    page_size: int = Field(
        default=10,
        description="Number of results per page",
        ge=1,
        le=100,
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Field to sort results by",
    )


@tool(args_schema=PaginationInput)
def paginated_list_api_call(
    query: str,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
) -> str:
    """
    Call a paginated list endpoint with offset-based pagination.

    This tool handles pagination automatically, allowing users to navigate
    through large result sets page by page.

    Args:
        query: Search query or filter criteria.
        page: Page number (1-based, default: 1).
        page_size: Number of results per page (1-100, default: 10).
        sort_by: Optional field name to sort results by.

    Returns:
        JSON string containing paginated results with metadata.

    Example:
        >>> paginated_list_api_call("customers", page=2, page_size=20)
        "{'items': [...], 'page': 2, 'total': 150, 'has_next': True}"
    """
    # Calculate offset for API call
    offset = (page - 1) * page_size

    # TODO: Build API request
    # 1. Construct query parameters with offset and limit
    # 2. Add sort parameter if provided
    # 3. Make API request
    # 4. Parse response with pagination metadata

    # Example response structure
    response_data = {
        "items": [f"item_{i}" for i in range(page_size)],
        "page": page,
        "page_size": page_size,
        "total_results": 150,
        "total_pages": (150 + page_size - 1) // page_size,
        "has_next": page < (150 + page_size - 1) // page_size,
        "has_previous": page > 1,
    }

    return str(response_data)


def handle_cursor_pagination(
    api_endpoint: str,
    query: str,
    max_results: int = 100,
    cursor: Optional[str] = None,
) -> Dict:
    """
    Handle cursor-based pagination.

    Some APIs use cursor-based pagination instead of offset-based.
    This function provides a pattern for handling such pagination.

    Args:
        api_endpoint: The API endpoint URL.
        query: Search query.
        max_results: Maximum number of results to retrieve.
        cursor: Cursor token from previous response (for subsequent requests).

    Returns:
        Dictionary with results and next_cursor for pagination.

    Example:
        >>> handle_cursor_pagination("https://api.example.com/items", "search", 50)
        {'items': [...], 'next_cursor': 'cursor_token_xyz'}
    """
    # TODO: Implement cursor-based pagination
    # 1. Build query parameters with cursor if provided
    # 2. Make API request
    # 3. Extract next_cursor from response
    # 4. Return results and cursor for next call

    return {
        "items": [],
        "next_cursor": None,
        "has_more": False,
    }


def get_all_paginated_results(
    api_call_func,
    query: str,
    max_pages: Optional[int] = None,
    **kwargs,
) -> List[Dict]:
    """
    Retrieve all paginated results by making multiple API calls.

    This helper function automatically fetches all pages of results,
    useful for getting complete datasets from paginated endpoints.

    Args:
        api_call_func: Function that makes the paginated API call.
        query: Search query.
        max_pages: Maximum number of pages to fetch (None for all).
        **kwargs: Additional arguments for the API call function.

    Returns:
        List of all results from all pages.

    Example:
        >>> all_results = get_all_paginated_results(
        ...     paginated_list_api_call,
        ...     "customers",
        ...     max_pages=5
        ... )
    """
    all_results = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            break

        # Make API call for current page
        result = api_call_func(query, page=page, **kwargs)

        # Parse result and extract items
        # TODO: Parse and extract items based on API response format

        # Check if there are more pages
        # TODO: Check if has_next or similar indicator

        page += 1

    return all_results
