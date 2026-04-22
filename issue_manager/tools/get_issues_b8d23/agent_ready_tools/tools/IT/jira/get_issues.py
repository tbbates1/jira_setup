
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
from ibm_watsonx_orchestrate.run.context import AgentRun

from agent_ready_tools.clients.error_handling import ErrorDetails
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.IT.jira.dynamic_schemas import (
    GET_ISSUES_DYNAMIC_INPUT_SCHEMA,
    GET_ISSUES_DYNAMIC_OUTPUT_SCHEMA,
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
    dynamic_input_schema=GET_ISSUES_DYNAMIC_INPUT_SCHEMA,
    dynamic_output_schema=GET_ISSUES_DYNAMIC_OUTPUT_SCHEMA,
)
def get_issues(
    current_run: AgentRun,
    project_name: str,
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    **kwargs: Any,
) -> dict:
    """
    Retrieves a list of issues in jira, with optional search and pagination.

    Args:
        current_run: AgentRun object containing the dynamic input and output schemas.
        project_name: The name of the project in Jira, returned by the `get_projects` tool.
        limit: The maximum number of issues to retrieve in a single API call.
        skip: The number of issues to skip for pagination.
        kwargs: Additional dynamic input parameters for issues.

    Returns:
        ToolResponse containing a list of issues objects or comments of a specific issue.
    """
    # Extract dynamic input and output parameters
    params_result = get_dynamic_params(current_run)
    if isinstance(params_result, ErrorDetails):
        return ToolResponse(error_details=params_result, tool_output=None).model_dump()

    dynamic_input_params, dynamic_output_params = params_result

    fields = list(dynamic_output_params)

    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(error_details=client, tool_output=None).model_dump()

        # Build params dict with dynamic input parameters
        params: dict[str, Any] = {
            "fields": fields,
            "maxResults": limit if not is_empty_value(limit) else 10,
            "startAt": skip if not is_empty_value(skip) else 0,
        }

        params["jql"] = f"project='{project_name}'"

        # Add dynamic input parameters from kwargs
        for param_name in dynamic_input_params:
            if param_name in kwargs and kwargs[param_name] is not None:
                if param_name == "issue_number":
                    params["jql"] = f"project='{project_name}' AND key='{kwargs[param_name]}'"
                else:
                    # Direct mapping for other fields
                    params[param_name] = kwargs[param_name]

        params = {key: value for key, value in params.items() if not is_empty_value(value)}

        response = client.get_request("search/jql", params=params)
        if isinstance(response, ErrorDetails):
            return ToolResponse(error_details=response, tool_output=None).model_dump()

        results: list[dict[str, Any]] = []

        # Process each issue in the response
        for issue in response.get("issues", []):
            # Build immutable outputs
            item: dict[str, Any] = {"issue_id": issue.get("id"), "issue_key": issue.get("key")}

            for field in fields:
                item[field] = issue.get("fields", {}).get(field)

            # Build dynamic outputs based on the fields specified in the dynamic output schema
            item = add_dynamic_output_params(
                base_output=item,
                api_result=issue.get("fields", {}),
                dynamic_output_params=dynamic_output_params,
                field_name_converter=None,
                nested_value_key="name",
            )

            results.append(item)

        return ToolResponse(tool_output=results, error_details=None).model_dump()

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while fetching Jira issues",
                details=str(e),
                url=None,
                recommendation="Check Jira API availability and credentials",
            ),
        ).model_dump()
