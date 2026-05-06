"""
> [!NOTE]
> This endpoint is in public preview and is subject to change.

Starts a new Copilot cloud agent task for a repository.

This endpoint is only available to users with a Copilot Business or Copilot Enterprise subscription.

**Fine-grained access tokens for "Start a task"**

This endpoint works with the following fine-grained token types:

* [GitHub App user access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
* [Fine-grained personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)

The fine-grained token must have the following permission set:

* "Agent tasks" repository permissions (read and write)

GitHub App installation access tokens are not supported for this endpoint.


Generated draft for LangChain Python tools.
"""

from __future__ import annotations

import json
from pydantic import BaseModel, Field
from langchain.tools import tool

class GithubAgentTasksCreateTaskInRepoInput(BaseModel):
    """Input schema for `github_agent_tasks_create_task_in_repo`."""

    owner: str = Field(..., description="The account owner of the repository. The name is not case sensitive. (source: path).")
    repo: str = Field(..., description="The name of the repository. The name is not case sensitive. (source: path).")

@tool(args_schema=GithubAgentTasksCreateTaskInRepoInput)
def github_agent_tasks_create_task_in_repo(owner: str, repo: str) -> str:
    """
    > [!NOTE]
> This endpoint is in public preview and is subject to change.

Starts a new Copilot cloud agent task for a repository.

This endpoint is only available to users with a Copilot Business or Copilot Enterprise subscription.

**Fine-grained access tokens for "Start a task"**

This endpoint works with the following fine-grained token types:

* [GitHub App user access tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
* [Fine-grained personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)

The fine-grained token must have the following permission set:

* "Agent tasks" repository permissions (read and write)

GitHub App installation access tokens are not supported for this endpoint.


    Args:
        owner: The account owner of the repository. The name is not case sensitive. (source: path).
        repo: The name of the repository. The name is not case sensitive. (source: path).

    Returns:
        JSON string with the standard success/data/error/metadata envelope.
    """
    # TODO: Replace this draft with a real API request.
    payload = {
        "success": True,
        "data": {
            "operation": "github_agent_tasks_create_task_in_repo",
            "method": "POST",
            "path": "/agents/repos/{owner}/{repo}/tasks",
            "request": {
                "owner": owner,
                "repo": repo,
            },
        },
        "error": None,
        "metadata": {"draft": True},
    }
    return json.dumps(payload)
