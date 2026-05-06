"""
Async LangChain tool variant.

This template demonstrates how to create asynchronous LangChain tools
for handling long-running operations and concurrent API calls.
"""

import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool


class AsyncToolInput(BaseModel):
    """Input schema for async tool."""

    query: str = Field(..., description="Search query")
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        ge=1,
        le=300,
    )
    parallel_requests: int = Field(
        default=1,
        description="Number of parallel requests to make",
        ge=1,
        le=10,
    )


@tool(args_schema=AsyncToolInput)
async def async_api_call(
    query: str,
    timeout: int = 30,
    parallel_requests: int = 1,
) -> str:
    """
    Asynchronously call an enterprise API endpoint.

    This tool uses async/await for non-blocking I/O operations,
    allowing for efficient handling of multiple concurrent requests.

    Args:
        query: Search query or filter criteria.
        timeout: Request timeout in seconds (1-300, default: 30).
        parallel_requests: Number of parallel requests (1-10, default: 1).

    Returns:
        A formatted string containing the combined API response data.

    Note:
        This tool is better suited for long-running operations or
        when making multiple concurrent API calls.

    Example:
        >>> import asyncio
        >>> result = asyncio.run(async_api_call("test", timeout=10, parallel_requests=3))
    """
    # TODO: Implement async API call logic
    # 1. Create multiple async tasks for parallel requests
    # 2. Set timeout for requests
    # 3. Use asyncio.gather() to run tasks concurrently
    # 4. Handle partial failures gracefully
    # 5. Combine and return results

    tasks = [
        make_async_request(query, timeout)
        for _ in range(parallel_requests)
    ]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.TimeoutError:
        return f"Request timeout after {timeout} seconds"

    return f"Async results: {results}"


async def make_async_request(query: str, timeout: int) -> str:
    """
    Make a single async HTTP request.

    Args:
        query: Query parameter.
        timeout: Request timeout in seconds.

    Returns:
        API response data.
    """
    # TODO: Implement actual async HTTP call using aiohttp
    # Example pattern:
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(url, timeout=timeout) as response:
    #         return await response.json()

    await asyncio.sleep(0.1)  # Simulate async work
    return f"Result for: {query}"


async def batch_async_api_calls(queries: list, max_concurrent: int = 5) -> list:
    """
    Make multiple async API calls with concurrency control.

    This function allows limiting the number of concurrent requests
    to avoid overwhelming the API or rate limiting.

    Args:
        queries: List of queries to process.
        max_concurrent: Maximum number of concurrent requests.

    Returns:
        List of results in the same order as input queries.

    Example:
        >>> results = asyncio.run(batch_async_api_calls(
        ...     ["query1", "query2", "query3"],
        ...     max_concurrent=3
        ... ))
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_call(query: str) -> str:
        async with semaphore:
            return await make_async_request(query, timeout=30)

    tasks = [bounded_call(query) for query in queries]
    return await asyncio.gather(*tasks, return_exceptions=True)


class AsyncBatchProcessor:
    """Helper class for processing items asynchronously in batches."""

    def __init__(self, max_concurrent: int = 5, timeout: int = 30):
        """
        Initialize batch processor.

        Args:
            max_concurrent: Maximum concurrent requests.
            timeout: Timeout per request in seconds.
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(self, items: list) -> list:
        """
        Process a batch of items asynchronously.

        Args:
            items: List of items to process.

        Returns:
            List of processed results.
        """
        tasks = [self._process_item(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_item(self, item: str) -> str:
        """
        Process a single item with concurrency control.

        Args:
            item: Item to process.

        Returns:
            Processed result.
        """
        async with self.semaphore:
            return await make_async_request(item, self.timeout)


if __name__ == "__main__":
    # Test async tool
    result = asyncio.run(async_api_call("test", timeout=10, parallel_requests=2))
    print(result)
