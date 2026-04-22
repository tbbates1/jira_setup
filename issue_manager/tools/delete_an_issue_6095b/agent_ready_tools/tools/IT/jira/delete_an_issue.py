
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
    
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from pydantic.dataclasses import dataclass

from agent_ready_tools.clients.error_handling import ErrorDetails
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.tool_response import ToolResponse


@dataclass
class DeleteIssueResponse:
    """Represents the result of delete an issue operation in Jira."""

    http_code: int


@tool(expected_credentials=JIRA_CONNECTIONS)
def delete_an_issue(
    issue_number: str, delete_sub_tasks: Optional[bool] = True
) -> ToolResponse[DeleteIssueResponse]:
    """
    Deletes an issue in Jira.

    Args:
        issue_number: The issue number uniquely identifying the issue, returned by `get_issues`
            tool.
        delete_sub_tasks: Indicates whether to also delete the subtasks of an issue.

    Returns:
        ToolResponse containing the result of performing the delete operation on an issue or error information.
    """

    if delete_sub_tasks:
        delete_sub_tasks_str = "true"
    else:
        delete_sub_tasks_str = "false"

    client = get_jira_client()
    if isinstance(client, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=client)

    response = client.delete_request(
        entity=f"issue/{issue_number}?deleteSubtasks={delete_sub_tasks_str}"
    )
    if isinstance(response, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=response)

    return ToolResponse(error_details=None, tool_output=DeleteIssueResponse(http_code=response))
