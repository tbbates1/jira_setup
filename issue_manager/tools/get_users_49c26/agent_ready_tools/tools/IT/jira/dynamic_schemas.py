"""
Dynamic schemas for Jira tools.

This module contains the dynamic input and output schema definitions for Jira tools that support
dynamic parameters. These schemas are used in both the tool definitions and tests.
"""

# Get projects dynamic schemas
GET_PROJECTS_DYNAMIC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_name": {
            "type": "string",
            "description": "The name of the project to search for",
        },
    },
}

GET_PROJECTS_DYNAMIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "error_details": {
            "type": "object",
            "properties": {},
            "additional_properties": True,
            "description": "Error details used to help the agent understand and navigate any tool or API issues",
        },
        "tool_output": {
            "type": "array",
            "description": "The output of the tool containing list of project objects",
            "items": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The name of the project",
                    },
                    "project_id": {
                        "type": "string",
                        "description": "The unique identifier of the project",
                    },
                    "project_key": {
                        "type": "string",
                        "description": "The unique key identifier for the project",
                    },
                    "project_lead": {
                        "type": "string",
                        "description": "The display name of the project lead",
                    },
                    "project_type": {
                        "type": "string",
                        "description": "The type of the project",
                    },
                },
                "additional_properties": True,
            },
        },
    },
    "required": ["project_name", "project_id"],
}

# Get users dynamic schemas
GET_USERS_DYNAMIC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "user_name": {
            "type": "string",
            "description": "The name of the user to search for",
        },
    },
}

GET_USERS_DYNAMIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "error_details": {
            "type": "object",
            "properties": {},
            "additional_properties": True,
            "description": "Error details used to help the agent understand and navigate any tool or API issues",
        },
        "tool_output": {
            "type": "array",
            "description": "The output of the tool containing list of user objects",
            "items": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "The unique account identifier of the user",
                    },
                    "user_name": {
                        "type": "string",
                        "description": "The display name of the user",
                    },
                    "email_address": {
                        "type": "string",
                        "description": "The email address of the user",
                    },
                    "account_type": {
                        "type": "string",
                        "description": "The type of the user account",
                    },
                    "active": {
                        "type": "boolean",
                        "description": "Whether the user is active or not",
                    },
                },
                "additional_properties": True,
            },
        },
    },
    "required": ["account_id", "user_name", "email_address"],
}

# Get Issue dynamic input schemas
GET_ISSUES_DYNAMIC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "issue_number": {
            "type": "string",
            "description": "The Jira issue key (e.g., ABC-123).",
        },
    },
}

# Get Issue dynamic output schemas
GET_ISSUES_DYNAMIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "error_details": {
            "type": "object",
            "properties": {},
            "additional_properties": True,
            "description": "Error details used to help the agent understand and navigate any tool or API issues",
        },
        "tool_output": {
            "type": "array",
            "description": "The output of the tool containing list of issue objects",
            "items": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Short summary of the issue",
                    },
                    "description": {
                        "type": "string",
                        "description": "The detailed description of the issue",
                    },
                    "progress": {
                        "type": "object",
                        "description": "The progress of the issue",
                        "properties": {
                            "progress": {
                                "type": "number",
                                "description": "The amount of progress made on the issue",
                            },
                        },
                    },
                    "attachment": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The attachments of the issue",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The labels of the issue",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date of the issue",
                    },
                    "status": {
                        "type": "string",
                        "description": "Current status of the issue",
                    },
                    "assignee": {
                        "type": "string",
                        "description": "User assigned to the issue",
                    },
                    "created": {
                        "type": "string",
                        "description": "Created date of the issue",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority of the issue",
                    },
                    "comment": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Comment of the issue",
                    },
                },
            },
        },
    },
}

# Create Issue dynamic input schemas
CREATE_ISSUE_DYNAMIC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "description": "Label used to categorize the Jira issue.",
        },
        "priority": {
            "type": "string",
            "description": "Priority of the issue, returned by the tool `get_issue_priorities`.",
        },
        "parent_issue_key": {
            "type": "string",
            "description": "Parent issue key for sub-tasks (e.g., ABC-123).",
        },
        "assignee": {
            "type": "string",
            "description": "User to whom the issue is assigned.",
        },
        "due_date": {
            "type": "string",
            "description": "Due date of the issue in ISO 8601 format (YYYY-MM-DD).",
        },
    },
    "required": ["project_id", "issuetype_id", "summary", "description"],
}

# Create Issue dynamic output schemas
CREATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "error_details": {
            "type": "object",
            "properties": {},
            "additional_properties": True,
            "description": "Error details used to help the agent understand and navigate any tool or API issues",
        },
        "tool_output": {
            "type": "object",
            "description": "The output of the tool containing the created Jira issue details",
            "properties": {
                "issue_number": {
                    "type": "string",
                    "description": "The key of the created Jira issue (e.g., ABC-123).",
                },
                "http_code": {
                    "type": "integer",
                    "description": "HTTP status code returned after issue creation.",
                },
                "label": {
                    "type": "string",
                    "description": "Label used to categorize the Jira issue.",
                },
                "priority": {
                    "type": "string",
                    "description": "Priority of the issue, returned by the tool `get_issue_priorities`.",
                },
                "parent_issue_key": {
                    "type": "string",
                    "description": "Parent issue key for sub-tasks (e.g., ABC-123).",
                },
                "assignee": {
                    "type": "string",
                    "description": "User to whom the issue is assigned.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date of the issue in ISO 8601 format (YYYY-MM-DD).",
                },
            },
            "additional_properties": True,
        },
    },
    "required": ["issue_number", "project_id", "issuetype_id", "description", "summary"],
}

# Update Issue dynamic input schemas
UPDATE_ISSUE_DYNAMIC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Updated summary of the issue",
        },
        "description": {
            "type": "string",
            "description": "Updated description of the issue",
        },
        "due_date": {
            "type": "string",
            "description": "Due date in YYYY-MM-DD format",
        },
        "assignee": {
            "type": "string",
            "description": "Account ID of the assignee",
        },
        "label": {
            "type": "string",
            "description": "Label to add to the issue",
        },
        "priority": {
            "type": "string",
            "description": "Priority of the issue",
        },
        "comment": {
            "type": "string",
            "description": "Comment to add to the issue",
        },
    },
    "required": ["issue_number"],
}

# Update Issue dynamic output schemas
UPDATE_ISSUE_DYNAMIC_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "tool_output": {
            "type": "object",
            "properties": {
                "http_code": {
                    "type": "integer",
                    "description": "HTTP status code returned by Jira",
                }
            },
            "additional_properties": False,
        },
        "error_details": {
            "type": "object",
            "additional_properties": True,
        },
        "summary": {
            "type": "string",
            "description": "Updated summary of the issue",
        },
        "description": {
            "type": "string",
            "description": "Updated description of the issue",
        },
        "due_date": {
            "type": "string",
            "description": "Due date in YYYY-MM-DD format",
        },
        "account_id": {
            "type": "string",
            "description": "Account ID of the assignee",
        },
        "label": {
            "type": "string",
            "description": "Label to add to the issue",
        },
        "priority": {
            "type": "string",
            "description": "Priority of the issue",
        },
        "comment": {
            "type": "string",
            "description": "Comment to add to the issue",
        },
    },
    "required": ["issue_number", "http_code"],
}
