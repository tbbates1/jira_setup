
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
    
from typing import List

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from pydantic.dataclasses import dataclass

from agent_ready_tools.clients.error_handling import ErrorDetails, no_data_in_get_request
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.tool_response import ToolResponse


@dataclass
class ProjectIssueType:
    """Represents the details of the project issue types in Jira."""

    issuetype_id: str
    issuetype: str


@dataclass
class ProjectIssueTypesResponse:
    """Represents the response from getting project issue types in Jira."""

    project_issue_types: List[ProjectIssueType]


@tool(expected_credentials=JIRA_CONNECTIONS)
def get_project_issue_types(project_id: str) -> ToolResponse[ProjectIssueTypesResponse]:
    """
    Retrieves a list of project issue types in Jira.

    Args:
        project_id: The ID of the project in Jira returned by the `get_projects` tool.

    Returns:
        ToolResponse containing a list of project issue types or error information.
    """

    client = get_jira_client()
    if isinstance(client, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=client)

    entity = f"issue/createmeta/{project_id}/issuetypes"

    response = client.get_request(entity=entity)
    if isinstance(response, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=response)

    project_issue_types: List[ProjectIssueType] = []
    for item in response.get("issueTypes", []):
        project_issue_types.append(
            ProjectIssueType(issuetype_id=item.get("id", ""), issuetype=item.get("name", ""))
        )

    if not project_issue_types:
        return ToolResponse(tool_output=None, error_details=no_data_in_get_request(response))

    return ToolResponse(
        error_details=None,
        tool_output=ProjectIssueTypesResponse(project_issue_types=project_issue_types),
    )
