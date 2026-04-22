
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
class GetIssuePriorities:
    """Represents a project in Jira."""

    name: str


@dataclass
class GetIssuePrioritiesResponse:
    """Represents the response for retrieving projects in Jira."""

    priorities: List[GetIssuePriorities]


@tool(expected_credentials=JIRA_CONNECTIONS)
def get_issue_priorities() -> ToolResponse[GetIssuePrioritiesResponse]:
    """
    Retrieves the list of priorities for an issue in Jira.

    Returns:
        ToolResponse containing the list of issue priorities or error information.
    """
    client = get_jira_client()
    if isinstance(client, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=client)

    response = client.get_request(entity="priority")
    if isinstance(response, ErrorDetails):
        return ToolResponse(tool_output=None, error_details=response)

    priorities: List[GetIssuePriorities] = []
    for result in response:
        if isinstance(result, dict):
            priorities.append(
                GetIssuePriorities(
                    name=result.get("name", ""),
                )
            )

    if not priorities:
        return ToolResponse(tool_output=None, error_details=no_data_in_get_request(response))

    return ToolResponse(
        error_details=None, tool_output=GetIssuePrioritiesResponse(priorities=priorities)
    )
