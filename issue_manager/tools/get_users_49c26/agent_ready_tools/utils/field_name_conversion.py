"""Utility functions for converting field names between different formats."""


def to_pascal_case(param_name: str) -> str:
    """
    Convert Python parameter name to PascalCase (used by Salesforce and other APIs). Handles
    snake_case to PascalCase conversion.

    Args:
        param_name: Python parameter name (e.g., 'close_date', 'stage_name', 'type')

    Returns:
        PascalCase field name (e.g., 'CloseDate', 'StageName', 'Type')

    Examples:
        >>> to_pascal_case('close_date')
        'CloseDate'
        >>> to_pascal_case('stage_name')
        'StageName'
        >>> to_pascal_case('type')
        'Type'
        >>> to_pascal_case('AccountId')  # Already in correct format
        'AccountId'
    """
    # If already in correct format (no underscores, starts with capital), return as-is
    if "_" not in param_name and param_name[0].isupper():
        return param_name

    # Convert snake_case to PascalCase
    return "".join(word.capitalize() for word in param_name.split("_"))


def to_camel_case(param_name: str) -> str:
    """
    Convert Python parameter name to camelCase (used by Workday and other APIs). Handles snake_case
    to camelCase conversion.

    Args:
        param_name: Python parameter name (e.g., 'close_date', 'stage_name', 'type')

    Returns:
        camelCase field name (e.g., 'closeDate', 'stageName', 'type')

    Examples:
        >>> to_camel_case('close_date')
        'closeDate'
        >>> to_camel_case('stage_name')
        'stageName'
        >>> to_camel_case('type')
        'type'
        >>> to_camel_case('accountId')  # Already in correct format
        'accountId'
    """
    # If already in correct format (no underscores, starts with lowercase), return as-is
    if "_" not in param_name and param_name[0].islower():
        return param_name

    # Convert snake_case to camelCase
    words = param_name.split("_")
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_dynamics365_field_name(param_name: str) -> str:
    """
    Convert Python parameter name to Dynamics365 syntax.

    Args:
        param_name: Python parameter name (e.g., 'number_of_employees', 'address_city', 'type')

    Returns:
        Dynamics 365 syntax fieldname (e.g., 'numberofemployees', 'address1_city', 'type')

    Examples:
        >>> to_dynamics365_field_name('number_of_employees')
        'numberofemployees'
        >>> to_dynamics365_field_name('address_city')
        'address1_city'
        >>> to_dynamics365_field_name('revenue')
        'revenue'
    """

    if param_name == "address":
        return "address1_composite"
    elif "address" in param_name:
        return param_name.replace("address", "address1")
    elif "telephone" in param_name:
        return param_name.replace("telephone", "telephone1")
    elif "_" not in param_name:
        return param_name
    else:
        param_name = "".join(param_name.split("_"))

    lookup_property_fields = {
        "primarycontactid",
        "customerid",
        "createdby",
        "ownerid",
        "parentaccountid",
        "parentcontactid",
    }

    if param_name in lookup_property_fields:
        return "_" + param_name + "_value"

    return param_name


def to_pascal_case_special_salesforce(param_name: str) -> str:
    """
    A special case of the genric "to_pascal_case" function for specific field names in Salesforce.
    Note: Some of the ID related fields cannot use "to_pascal_case" directly because:
        1. They are ID fields and we disambiguate the naming of the field in our function call as compared to the Salesforce API
        2. We shorten the naming of the field in our function call as compared to the Salesforce API

    Args:
        param_name: Python parameter name (e.g., 'close_date', 'stage_name', 'type')

    Returns:
        PascalCase field name (e.g., 'CloseDate', 'StageName', 'Type')
    """
    special_cases = {
        "contact_id": "WhoId",
        "account_id": "WhatId",
        "assignee_id": "OwnerId",
        "duration_in_mins": "DurationInMinutes",
        "activity_date": "ActivityDateTime",
        "time_zone": "TimeZoneSidKey",
        "due_date": "ActivityDate",
    }

    # Return from dictionary if it exists, otherwise use standard conversion
    return special_cases.get(param_name, to_pascal_case(param_name))
