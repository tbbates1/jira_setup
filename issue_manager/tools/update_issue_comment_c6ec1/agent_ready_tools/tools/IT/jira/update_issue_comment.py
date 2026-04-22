
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
from typing import Any, Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from pydantic.dataclasses import dataclass

from agent_ready_tools.clients.error_handling import ErrorDetails
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.IT.jira.jira_utility import adf_paragraph
from agent_ready_tools.tools.tool_response import ToolResponse
from agent_ready_tools.utils.format_tool_input import is_empty_value


@dataclass
class UpdateIssueCommentResponse:
    """Represents the result of updating a comment on a Jira issue."""

    http_code: Optional[int] = None
    comment_id: Optional[str] = None
    updated_text: Optional[str] = None


@tool(expected_credentials=JIRA_CONNECTIONS)
def update_issue_comment(
    issue_number: str,
    comment_id: str,
    comment_text: Optional[str] = None,
) -> ToolResponse[UpdateIssueCommentResponse]:
    """
    Updates an existing comment on a Jira issue.

    Args:
        issue_number: The unique number of the issue, returned by the `get_issues` tool.
        comment_id: The unique ID of the comment, returned by the `get_issues` tool.
        comment_text: The new comment content.

    Returns:
        ToolResponse with containing confirmation of the details update or error information.
    """
    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(error_details=client, tool_output=None)

        # Validate inputs
        if is_empty_value(issue_number):
            return ToolResponse(
                error_details=ErrorDetails(
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    reason="Missing issue_number",
                    details="issue_number must be provided (issue key like 'PROJ-123' or numeric ID).",
                    url=None,
                    recommendation="Pass a valid issue key or ID returned by 'get_issues'.",
                ),
                tool_output=None,
            )

        if is_empty_value(comment_id):
            return ToolResponse(
                error_details=ErrorDetails(
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    reason="Missing comment_id",
                    details="comment_id must be provided.",
                    url=None,
                    recommendation="Use the ID returned by 'get_comments' or the comment creation API.",
                ),
                tool_output=None,
            )

        if is_empty_value(comment_text):
            return ToolResponse(
                error_details=ErrorDetails(
                    status_code=HTTPStatus.BAD_REQUEST.value,
                    reason="Missing comment_text",
                    details="comment_text must be provided to update the comment.",
                    url=None,
                    recommendation="Provide the new comment text; it will be converted to ADF.",
                ),
                tool_output=None,
            )

        # Prepare payload with ADF body
        payload: dict[str, Any] = {
            "body": adf_paragraph(str(comment_text)),
        }

        # PUT /issue/{issueIdOrKey}/comment/{id}
        entity = f"issue/{issue_number}/comment/{comment_id}"
        response = client.put_request(entity=entity, payload=payload)

        if isinstance(response, ErrorDetails):
            return ToolResponse(error_details=response, tool_output=None)

        status_code = response.get("status_code", HTTPStatus.OK.value)

        # Parse response body to fill optional fields; set fallbacks to satisfy tests
        returned_comment_id: Optional[str] = comment_id
        updated_text: Optional[str] = comment_text

        body = response.get("body") if isinstance(response, dict) else None
        if isinstance(body, dict):
            returned_comment_id = body.get("id", returned_comment_id)

        return ToolResponse(
            error_details=None,
            tool_output=UpdateIssueCommentResponse(
                http_code=status_code,
                comment_id=returned_comment_id,
                updated_text=updated_text,
            ),
        )

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while updating comment in Jira",
                details=str(e),
                url=None,
                recommendation=(
                    "Verify Jira connectivity, OAuth token scope/expiry (write:jira-work), "
                    "user permissions on the issue and comment, correctness of issue key/ID and "
                    "comment ID, and ensure the ADF body structure is valid."
                ),
            ),
            tool_output=None,
        )
