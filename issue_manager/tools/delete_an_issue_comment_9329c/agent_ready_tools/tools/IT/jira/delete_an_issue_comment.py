
from pathlib import Path
import sys

test_dir = Path(__file__).parent
BASE_DIR = 'agent_ready_tools'
MAX_DEPTH = 10

while test_dir.name != BASE_DIR:
    test_dir = test_dir.parent
    MAX_DEPTH -= 1
    if MAX_DEPTH == 0:
        raise RecursionError(f"'{BASE_DIR}' not found in path: {__file__}")
parent_path = test_dir.parent.resolve()

sys.path.append(str(parent_path))
    
from http import HTTPStatus
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from pydantic.dataclasses import dataclass

from agent_ready_tools.clients.error_handling import ErrorDetails
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.tool_response import ToolResponse


@dataclass
class DeleteCommentResponse:
    """Represents the result of deleting a comment in Jira."""

    http_code: Optional[int]


@tool(expected_credentials=JIRA_CONNECTIONS)
def delete_an_issue_comment(
    issue_number: str,
    comment_id: str,
) -> ToolResponse[DeleteCommentResponse]:
    """
    Deletes a comment from a Jira issue.

    Args:
        issue_number: The issue number uniquely identifying the issue, returned by `get_issues`.
        comment_id: The comment ID uniquely identifying the comment, returned by `get_comments`.

    Returns:
        ToolResponse containing the result of deleting a comment in Jira.
    """
    client = get_jira_client()
    if isinstance(client, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=client)

    try:
        response = client.delete_request(entity=f"issue/{issue_number}/comment/{comment_id}")
        if isinstance(response, ErrorDetails):
            return ToolResponse(tool_output=None, error_details=response)

        return ToolResponse(
            error_details=None,
            tool_output=DeleteCommentResponse(
                http_code=(
                    response
                    if isinstance(response, int)
                    else response.get("status_code", HTTPStatus.INTERNAL_SERVER_ERROR.value)
                )
            ),
        )

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while deleting a comment from a Jira issue.",
                details=str(e),
                url=None,
                recommendation="Check Jira connectivity, credentials, and API permissions.",
            ),
        )
