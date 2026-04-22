
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

from agent_ready_tools.clients.error_handling import ErrorDetails, no_data_in_get_request
from agent_ready_tools.clients.jira_client import JIRA_CONNECTIONS, get_jira_client
from agent_ready_tools.tools.IT.jira.dynamic_schemas import (
    GET_USERS_DYNAMIC_INPUT_SCHEMA,
    GET_USERS_DYNAMIC_OUTPUT_SCHEMA,
)
from agent_ready_tools.tools.tool_response import ToolResponse
from agent_ready_tools.utils.dynamic_params_utils import (
    add_dynamic_output_params,
    get_dynamic_params,
)
from agent_ready_tools.utils.field_name_conversion import to_camel_case
from agent_ready_tools.utils.format_tool_input import is_empty_value

_ACCOUNT_TYPE: str = "app"


@tool(
    expected_credentials=JIRA_CONNECTIONS,
    enable_dynamic_input_schema=True,
    enable_dynamic_output_schema=True,
    dynamic_input_schema=GET_USERS_DYNAMIC_INPUT_SCHEMA,
    dynamic_output_schema=GET_USERS_DYNAMIC_OUTPUT_SCHEMA,
)
def get_users(
    current_run: AgentRun,
    limit: Optional[int] = 40,
    skip: Optional[int] = 0,
    **kwargs: Any,
) -> dict:
    """
    Retrieves all users from Jira.

    Args:
        current_run: AgentRun object containing the dynamic input and output schemas.
        limit: The maximum number of users to retrieve in a single API call.
        skip: The number of users to skip for pagination.
        kwargs: Additional dynamic input parameters for the users.

    Returns:
        ToolResponse containing list of users or error information.
    """
    # Extract dynamic input and output parameters
    params_result = get_dynamic_params(current_run)
    if isinstance(params_result, ErrorDetails):
        return ToolResponse(error_details=params_result, tool_output=None).model_dump()

    dynamic_input_params, dynamic_output_params = params_result

    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(tool_output=None, error_details=client).model_dump()

        # Build params dict with dynamic input parameters
        params = {
            "maxResults": limit if not is_empty_value(limit) else 40,
            "startAt": skip if not is_empty_value(skip) else 0,
        }

        # Add dynamic input parameters from kwargs
        for param_name in dynamic_input_params:
            if param_name in kwargs and kwargs[param_name] is not None:
                if param_name == "user_name":
                    params["query"] = kwargs[param_name]
                else:
                    # Direct mapping for other fields
                    params[param_name] = kwargs[param_name]

        params = {key: value for key, value in params.items() if not is_empty_value(value)}

        response = client.get_request(entity="users/search", params=params)
        if isinstance(response, ErrorDetails):
            return ToolResponse(tool_output=None, error_details=response).model_dump()

        users: list[dict[str, Any]] = []

        for result in response:
            if isinstance(result, dict):
                if result.get("accountType", "") != _ACCOUNT_TYPE:
                    # Build user with immutable outputs
                    user: dict[str, Any] = {
                        "account_id": result.get("accountId", ""),
                        "user_name": result.get("displayName", ""),
                        "email_address": result.get("emailAddress", ""),
                    }

                    # Add dynamic output parameters using helper function
                    user = add_dynamic_output_params(
                        base_output=user,
                        api_result=result,
                        dynamic_output_params=dynamic_output_params,
                        field_name_converter=to_camel_case,
                        nested_value_key=None,
                    )

                    users.append(user)

        if not users:
            return ToolResponse(
                tool_output=None, error_details=no_data_in_get_request(response)
            ).model_dump()

        return ToolResponse(error_details=None, tool_output=users).model_dump()

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="Exception occurred while retrieving users",
                details=str(e),
                url=None,
                recommendation="Check network connectivity, credentials, and API permissions.",
            ),
        ).model_dump()
