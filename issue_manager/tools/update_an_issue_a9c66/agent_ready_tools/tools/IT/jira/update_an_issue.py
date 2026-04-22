
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
    UPDATE_ISSUE_DYNAMIC_INPUT_SCHEMA,
    UPDATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA,
)
from agent_ready_tools.tools.IT.jira.jira_utility import adf_paragraph
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
    dynamic_input_schema=UPDATE_ISSUE_DYNAMIC_INPUT_SCHEMA,
    dynamic_output_schema=UPDATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA,
)
def update_an_issue(
    issue_number: str,
    current_run: AgentRun,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Updates the issue details in jira.

    Args:
        issue_number: The issue number uniquely identifying the issue, returned by the `get_issues` tool.
        current_run: AgentRun object containing the dynamic input and output schemas.
        kwargs: Additional dynamic input parameters for the issue.

    Returns:
        The result of the issue update operation.
    """
    # Extract dynamic input & output parameters
    params_result = get_dynamic_params(current_run)
    if isinstance(params_result, ErrorDetails):
        return ToolResponse(error_details=params_result, tool_output=None).model_dump()

    dynamic_input_params, dynamic_output_params = params_result

    try:
        client = get_jira_client()
        if isinstance(client, ErrorDetails):
            return ToolResponse(tool_output=None, error_details=client).model_dump()

        # Jira update payload structure
        payload: dict[str, Any] = {}
        update_actions: dict[str, Any] = {}

        #  Add dynamic input parameters
        for param in dynamic_input_params:
            if param in kwargs and kwargs[param] is not None:
                if param == "summary":
                    payload["summary"] = kwargs[param]
                elif param == "description":
                    payload["description"] = adf_paragraph(str(kwargs[param]))
                elif param == "priority":
                    payload["priority"] = {"name": kwargs[param]}
                elif param == "due_date":
                    payload["duedate"] = kwargs[param]
                elif param == "assignee":
                    payload["assignee"] = {"accountId": kwargs[param]}
                # Map list-based operations to the 'update' object
                elif param == "label":
                    # Using 'add' ensures we don't delete existing labels on the issue
                    update_actions.setdefault("labels", []).append({"add": kwargs[param]})
                elif param == "comment":
                    # Comments must also be in ADF format and nested under the 'add'
                    update_actions.setdefault("comment", []).append(
                        {"add": {"body": adf_paragraph(str(kwargs[param]))}}
                    )
                else:
                    payload[param] = kwargs[param]

        # Remove empty values
        payload = {key: value for key, value in payload.items() if not is_empty_value(value)}
        final_request_body: dict[str, Any] = {}
        # Map standard fields into the mandatory 'fields' object
        if payload:
            final_request_body["fields"] = payload
        # Map additive operations into the 'update' object
        if update_actions:
            final_request_body["update"] = update_actions

        # Call Jira API
        response = client.put_request(
            entity=f"issue/{issue_number}",
            payload=final_request_body,
        )

        if isinstance(response, ErrorDetails):
            return ToolResponse(tool_output=None, error_details=response).model_dump()

        result = response.get("result", {})

        # Build output
        output: dict[str, Any] = {
            "http_code": response.get("status_code", HTTPStatus.NO_CONTENT.value),
            "issue_number": issue_number,
        }

        # Add dynamic output parameters (future-safe)
        output = add_dynamic_output_params(
            base_output=output,
            api_result=result,
            dynamic_output_params=dynamic_output_params,
            field_name_converter=None,
            nested_value_key="name",
        )

        return ToolResponse(error_details=None, tool_output=output).model_dump()

    except Exception as e:  # pylint: disable=broad-except
        return ToolResponse(
            tool_output=None,
            error_details=ErrorDetails(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                reason="An error occurred while updating Jira issue.",
                details=str(e),
                url=None,
                recommendation="Check Jira connectivity, permissions, and issue key.",
            ),
        ).model_dump()
