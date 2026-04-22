
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
    GET_PROJECTS_DYNAMIC_INPUT_SCHEMA,
    GET_PROJECTS_DYNAMIC_OUTPUT_SCHEMA,
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
    dynamic_input_schema=GET_PROJECTS_DYNAMIC_INPUT_SCHEMA,
    dynamic_output_schema=GET_PROJECTS_DYNAMIC_OUTPUT_SCHEMA,
)
def get_projects(
    current_run: AgentRun,
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    **kwargs: Any,
) -> dict:
    """
    Retrieves a list of projects in Jira.

    Args:
        current_run: AgentRun object containing the dynamic input and output schemas.
        limit: The maximum number of projects to retrieve in a single API call.
        skip: The number of projects to skip for pagination.
        kwargs: Additional dynamic input parameters for the Project.

    Returns:
        ToolResponse containing a list of project objects.
    """
    # Extract dynamic input and output parameters
    params_result = get_dynamic_params(current_run)
    if isinstance(params_result, ErrorDetails):
        return ToolResponse(error_details=params_result, tool_output=None).model_dump()

    dynamic_input_params, dynamic_output_params = params_result

    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(error_details=client, tool_output=None).model_dump()

        # Build params dict with dynamic input parameters
        params = {
            "expand": "lead",
            "maxResults": limit if not is_empty_value(limit) else 10,
            "startAt": skip if not is_empty_value(skip) else 0,
        }

        # Add dynamic input parameters from kwargs
        for param_name in dynamic_input_params:
            if param_name in kwargs and kwargs[param_name] is not None:
                if param_name == "project_name":
                    params["query"] = kwargs[param_name]
                else:
                    # Direct mapping for other fields
                    params[param_name] = kwargs[param_name]

        params = {key: value for key, value in params.items() if not is_empty_value(value)}

        response = client.get_request(entity="project/search", params=params)
        if isinstance(response, ErrorDetails):
            return ToolResponse(error_details=response, tool_output=None).model_dump()

        results: list[dict[str, Any]] = []

        for project in response.get("values", []):
            # Build project with immutable outputs
            item: dict[str, Any] = {
                "project_name": project.get("name", ""),
                "project_id": project.get("id", ""),
            }

            # Add dynamic output parameters using helper function
            item = add_dynamic_output_params(
                base_output=item,
                api_result=project,
                dynamic_output_params=dynamic_output_params,
                field_name_converter=lambda param: (
                    "key"
                    if param == "project_key"
                    else (
                        "lead"
                        if param == "project_lead"
                        else "projectTypeKey" if param == "project_type" else param
                    )
                ),
                nested_value_key="displayName",
            )

            results.append(item)

        return ToolResponse(tool_output=results, error_details=None).model_dump()

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while retrieving projects",
                details=str(e),
                url=None,
                recommendation="Check network connectivity, credentials, and API permissions.",
            ),
        ).model_dump()
