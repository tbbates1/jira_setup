
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
from typing import Any

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.run.context import AgentRun

from agent_ready_tools.clients.error_handling import ErrorDetails
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.IT.jira.dynamic_schemas import (
    CREATE_ISSUE_DYNAMIC_INPUT_SCHEMA,
    CREATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA,
)
from agent_ready_tools.tools.tool_response import ToolResponse
from agent_ready_tools.utils.dynamic_params_utils import (
    add_dynamic_output_params,
    get_dynamic_params,
)
from agent_ready_tools.utils.format_tool_input import is_empty_value


@tool(
    expected_credentials=JIRA_CONNECTIONS,
    enable_dynamic_input_schema=True,
    enable_dynamic_output_schema=True,
    dynamic_input_schema=CREATE_ISSUE_DYNAMIC_INPUT_SCHEMA,
    dynamic_output_schema=CREATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA,
)
def create_an_issue(
    project_id: str,
    issuetype_id: str,
    summary: str,
    description: str,
    current_run: AgentRun,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Creates an issue in jira.

    Args:
        project_id: The ID of the project in Jira, obtained by the `get_projects` tool.
        issuetype_id: The ID of the issue type in Jira, obtained by the `get_project_issue_types` tool.
        summary: The summary of the issue in Jira.
        description: A detailed explanation of the issue in Jira.
        current_run: AgentRun object containing the dynamic input and output schemas.
        kwargs: Additional dynamic input parameters for issues.

    Returns:
        ToolResponse containing the result from performing the creation of a issue.
    """

    # Extract dynamic input & output params
    params_result = get_dynamic_params(current_run)
    if isinstance(params_result, ErrorDetails):
        return ToolResponse(error_details=params_result, tool_output=None).model_dump()

    dynamic_input_params, dynamic_output_params = params_result

    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(error_details=client, tool_output=None).model_dump()

        # Immutable payload
        payload: dict[str, Any] = {
            "fields": {
                "project": {"id": project_id},
                "issuetype": {"id": issuetype_id},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
            }
        }

        # Add dynamic input parameters from kwargs
        for param in dynamic_input_params:
            if param in kwargs and kwargs[param] is not None:
                if param == "priority":
                    payload["fields"]["priority"] = {"name": kwargs[param]}
                elif param == "parent_issue_key":
                    payload["fields"]["parent"] = {"key": kwargs[param]}
                elif param == "assignee":
                    payload["fields"]["assignee"] = {"accountId": kwargs[param]}
                elif param == "label":
                    payload["fields"]["labels"] = [kwargs[param]]
                elif param == "due_date":
                    payload["fields"]["duedate"] = kwargs[param]
                else:
                    payload["fields"][param] = kwargs[param]

        # Remove empty values
        payload["fields"] = {
            key: value for key, value in payload["fields"].items() if not is_empty_value(value)
        }

        response = client.post_request(entity="issue", payload=payload)
        if isinstance(response, ErrorDetails):
            return ToolResponse(error_details=response, tool_output=None).model_dump()

        # Align API response with the 'result' variable used in dynamic output helpers.
        result = response

        output: dict[str, Any] = {
            "http_code": response.get("status_code"),
            "issue_number": result.get("key", ""),
            "project_id": project_id,
            "issuetype_id": issuetype_id,
            "description": description,
            "summary": summary,
        }

        # Add dynamic output parameters using helper function
        output = add_dynamic_output_params(
            base_output=output,
            api_result=result,
            dynamic_output_params=dynamic_output_params,
            field_name_converter=None,
            nested_value_key="name",
        )

        return ToolResponse(tool_output=output, error_details=None).model_dump()

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while creating Jira issue",
                details=str(e),
                url=None,
                recommendation="Check Jira API availability and credentials",
            ),
        ).model_dump()
