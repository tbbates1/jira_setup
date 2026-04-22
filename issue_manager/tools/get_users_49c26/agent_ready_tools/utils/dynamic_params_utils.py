"""
Utility functions for handling dynamic input and output parameters in tools.

This module provides reusable functions for extracting dynamic parameters from AgentRun objects,
which can be used across all tools that support dynamic schemas.
"""

from typing import Any, Callable, Optional

from ibm_watsonx_orchestrate.run.context import AgentRun

from agent_ready_tools.clients.error_handling import ErrorDetails


def get_dynamic_params(current_run: AgentRun) -> tuple[list[str], list[str]] | ErrorDetails:
    """
    Extract dynamic input and output parameters from the AgentRun object.

    This function handles different schema structures:
    - For output: Array structure (tool_output.items.properties), Object structure (tool_output.properties),
      or flat structure (top-level properties)
    - For input: Standard properties structure

    Args:
        current_run: AgentRun object containing the dynamic input and output schemas.

    Returns:
        A tuple of (dynamic_input_params, dynamic_output_params) as lists of parameter names,
        or ErrorDetails if extraction fails.
    """
    try:
        # Get dynamic input parameters
        if current_run.dynamic_input_schema:
            dynamic_input_params = list(current_run.dynamic_input_schema.properties.keys())
        else:
            dynamic_input_params = []

        # If dynamic output params are defined
        if current_run.dynamic_output_schema:
            # Try to get dynamic output params from nested structure
            tool_output_schema = current_run.dynamic_output_schema.properties.get("tool_output")
            if (
                tool_output_schema
                and hasattr(tool_output_schema, "items")
                and tool_output_schema.items
            ):
                # Array structure: tool_output is an array of items
                dynamic_output_params = list(tool_output_schema.items.properties.keys())
            elif (
                tool_output_schema
                and hasattr(tool_output_schema, "properties")
                and tool_output_schema.properties
            ):
                # Object structure: tool_output is an object with properties
                dynamic_output_params = list(tool_output_schema.properties.keys())
            else:
                # Fallback: properties at top level
                dynamic_output_params = list(current_run.dynamic_output_schema.properties.keys())

        else:
            dynamic_output_params = []

        return dynamic_input_params, dynamic_output_params

    except AttributeError as e:
        return ErrorDetails(
            status_code=None,
            url=None,
            reason="Dynamic parameters logic failed",
            details=f"AgentRun class doesn't have expected structure: {str(e)}",
            recommendation=f"Contact your administrator, as the structure is {current_run}",
        )


def add_dynamic_output_params(
    base_output: dict[str, Any],
    api_result: dict[str, Any],
    dynamic_output_params: list[str],
    field_name_converter: Optional[Callable[[str], str]] = None,
    nested_value_key: Optional[str] = None,
) -> dict[str, Any]:
    """
    Add dynamic output parameters from API result to the base output dictionary.

    Args:
        base_output: Dictionary containing the immutable/base output fields.
        api_result: Dictionary containing the API response data.
        dynamic_output_params: List of dynamic output parameter names to extract.
        field_name_converter: Optional function to convert parameter names to API field names.
                            If None, parameter names are used as-is.
        nested_value_key: Optional key to extract from nested dictionary values. When the API
                         returns a field as a dictionary (e.g., {"value": "actual_data"}),
                         this key specifies which nested field to extract. If None, the entire
                         value is used. Common examples: "value", "display_value", "name".

    Returns:
        The base_output dictionary with dynamic parameters added.
    """
    for param in dynamic_output_params:
        if param not in base_output:
            # Convert param name to API field name if converter provided
            api_field_name = field_name_converter(param) if field_name_converter else param

            # Handle nested dictionary values (e.g., {"value": "actual_data"})
            if isinstance(api_result.get(api_field_name), dict):
                if nested_value_key:
                    base_output[param] = api_result.get(api_field_name, {}).get(
                        nested_value_key, ""
                    )
                else:
                    base_output[param] = api_result.get(api_field_name, "")
            else:
                # Handle simple values (strings, numbers, booleans, lists, etc.)
                base_output[param] = api_result.get(api_field_name)

    return base_output
