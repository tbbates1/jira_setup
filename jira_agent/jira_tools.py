"""Jira tools for watsonx Orchestrate.

A self-contained toolkit covering full CRUD on Jira projects, issues, and
comments, backed by a custom OAuth2 Auth Code connection (`app_id="jira_lab"`).
Change JIRA_APP_ID below if you used a different app_id when running
`orchestrate connections add`.
"""
from typing import Optional
import requests

from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.agent_builder.connections import (
    ConnectionType,
    ExpectedCredentials,
)
from ibm_watsonx_orchestrate.run import connections

JIRA_APP_ID = "jira_lab"
JIRA_CONNECTIONS = [ExpectedCredentials(app_id=JIRA_APP_ID, type=ConnectionType.OAUTH2_AUTH_CODE)]


def _headers() -> dict:
    creds = connections.oauth2_auth_code(JIRA_APP_ID)
    return {
        "Authorization": f"Bearer {creds.access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _cloud_id(headers: dict) -> str:
    r = requests.get("https://api.atlassian.com/oauth/token/accessible-resources", headers=headers, timeout=15)
    r.raise_for_status()
    sites = r.json()
    if not sites:
        raise RuntimeError("No Atlassian sites accessible to this token.")
    return sites[0]["id"]


def _adf(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_get_projects(project_name: Optional[str] = None, limit: Optional[int] = 50) -> dict:
    """List Jira projects, optionally filtered by name substring.

    Args:
        project_name: Optional case-insensitive substring to filter by project name or key.
        limit: Max results to return (default 50).
    """
    h = _headers()
    cid = _cloud_id(h)
    r = requests.get(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/project/search",
        headers=h,
        params={"maxResults": limit or 50, **({"query": project_name} if project_name else {})},
        timeout=15,
    )
    r.raise_for_status()
    return {
        "projects": [
            {"project_id": p["id"], "project_key": p["key"], "project_name": p["name"]}
            for p in r.json().get("values", [])
        ]
    }


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_get_project_issue_types(project_id: str) -> dict:
    """Get the issue types available for a Jira project.

    Args:
        project_id: Numeric project ID.
    """
    h = _headers()
    cid = _cloud_id(h)
    r = requests.get(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issuetype/project",
        headers=h,
        params={"projectId": project_id},
        timeout=15,
    )
    r.raise_for_status()
    return {"issue_types": [{"issuetype_id": it["id"], "name": it["name"]} for it in r.json()]}


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_get_issue_priorities() -> dict:
    """List the issue priorities configured in this Jira instance."""
    h = _headers()
    cid = _cloud_id(h)
    r = requests.get(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/priority",
        headers=h,
        timeout=15,
    )
    r.raise_for_status()
    return {"priorities": [{"priority_id": p["id"], "name": p["name"]} for p in r.json()]}


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_get_users(user_name: Optional[str] = None, limit: Optional[int] = 50) -> dict:
    """List or search users in Jira.

    Args:
        user_name: Optional substring to search by display name or email.
        limit: Max users to return (default 50).
    """
    h = _headers()
    cid = _cloud_id(h)
    if user_name:
        r = requests.get(
            f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/user/search",
            headers=h,
            params={"query": user_name, "maxResults": limit or 50},
            timeout=15,
        )
    else:
        r = requests.get(
            f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/users/search",
            headers=h,
            params={"maxResults": limit or 50},
            timeout=15,
        )
    r.raise_for_status()
    return {
        "users": [
            {
                "account_id": u.get("accountId"),
                "display_name": u.get("displayName"),
                "email": u.get("emailAddress"),
                "active": u.get("active", True),
            }
            for u in r.json()
        ]
    }


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_create_issue(
    project_id: str,
    issuetype_id: str,
    summary: str,
    description: str,
    priority_id: Optional[str] = None,
    assignee_account_id: Optional[str] = None,
) -> dict:
    """Create a Jira issue.

    Args:
        project_id: Numeric project ID.
        issuetype_id: Numeric issue type ID.
        summary: Short title.
        description: Plain-text body.
        priority_id: Optional numeric priority ID.
        assignee_account_id: Optional Atlassian account ID for the assignee.
    """
    h = _headers()
    cid = _cloud_id(h)
    fields = {
        "project": {"id": project_id},
        "issuetype": {"id": issuetype_id},
        "summary": summary,
        "description": _adf(description),
    }
    if priority_id:
        fields["priority"] = {"id": priority_id}
    if assignee_account_id:
        fields["assignee"] = {"accountId": assignee_account_id}
    r = requests.post(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue",
        headers=h,
        json={"fields": fields},
        timeout=15,
    )
    if r.status_code >= 400:
        return {"error": r.status_code, "body": r.text}
    return r.json()


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_get_issues(
    project_key: str,
    limit: Optional[int] = 20,
    issue_key: Optional[str] = None,
) -> dict:
    """List recent issues for a project, or fetch a specific issue (with comments).

    Args:
        project_key: The project key, e.g. 'KAN'.
        limit: Max issues to return (when listing).
        issue_key: If provided (e.g. 'KAN-3'), returns just that issue with comments.
    """
    h = _headers()
    cid = _cloud_id(h)
    if issue_key:
        r = requests.get(
            f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}",
            headers=h,
            params={"fields": "summary,status,assignee,priority,comment"},
            timeout=15,
        )
        r.raise_for_status()
        issue = r.json()
        f = issue.get("fields", {})
        comments = []
        for c in (f.get("comment", {}) or {}).get("comments", []):
            body = c.get("body", {})
            text = ""
            if isinstance(body, dict):
                for blk in body.get("content", []):
                    for inner in blk.get("content", []):
                        if inner.get("type") == "text":
                            text += inner.get("text", "")
            comments.append(
                {
                    "comment_id": c.get("id"),
                    "author": (c.get("author") or {}).get("displayName"),
                    "created": c.get("created"),
                    "text": text,
                }
            )
        return {
            "key": issue.get("key"),
            "summary": f.get("summary"),
            "status": (f.get("status") or {}).get("name"),
            "assignee": (f.get("assignee") or {}).get("displayName"),
            "priority": (f.get("priority") or {}).get("name"),
            "comments": comments,
        }
    r = requests.get(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/search/jql",
        headers=h,
        params={
            "jql": f'project = "{project_key}" ORDER BY created DESC',
            "maxResults": limit or 20,
            "fields": "summary,status",
        },
        timeout=15,
    )
    r.raise_for_status()
    issues = []
    for issue in r.json().get("issues", []):
        f = issue.get("fields", {})
        issues.append(
            {
                "key": issue.get("key"),
                "summary": f.get("summary"),
                "status": (f.get("status") or {}).get("name"),
            }
        )
    return {"issues": issues}


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_update_issue(
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    priority_id: Optional[str] = None,
    assignee_account_id: Optional[str] = None,
    add_comment: Optional[str] = None,
) -> dict:
    """Update fields on an existing Jira issue, and/or add a comment.

    Args:
        issue_key: e.g. 'KAN-3'.
        summary: New summary (optional).
        description: New description (optional).
        priority_id: New priority ID (optional).
        assignee_account_id: New assignee account ID (optional).
        add_comment: If provided, posts this text as a new comment.
    """
    h = _headers()
    cid = _cloud_id(h)
    fields: dict = {}
    if summary is not None:
        fields["summary"] = summary
    if description is not None:
        fields["description"] = _adf(description)
    if priority_id is not None:
        fields["priority"] = {"id": priority_id}
    if assignee_account_id is not None:
        fields["assignee"] = {"accountId": assignee_account_id}

    results: dict = {"issue_key": issue_key}
    if fields:
        r = requests.put(
            f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}",
            headers=h,
            json={"fields": fields},
            timeout=15,
        )
        if r.status_code >= 400:
            return {"error": r.status_code, "body": r.text}
        results["updated"] = True

    if add_comment:
        r = requests.post(
            f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}/comment",
            headers=h,
            json={"body": _adf(add_comment)},
            timeout=15,
        )
        if r.status_code >= 400:
            return {"error": r.status_code, "body": r.text}
        results["comment_id"] = r.json().get("id")

    if not fields and not add_comment:
        results["error"] = "No fields provided to update."
    return results


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_delete_issue(issue_key: str) -> dict:
    """Delete a Jira issue by key.

    Args:
        issue_key: e.g. 'KAN-3'.
    """
    h = _headers()
    cid = _cloud_id(h)
    r = requests.delete(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}",
        headers=h,
        timeout=15,
    )
    if r.status_code == 204:
        return {"deleted": issue_key}
    return {"error": r.status_code, "body": r.text}


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_update_issue_comment(issue_key: str, comment_id: str, new_text: str) -> dict:
    """Update an existing comment on a Jira issue.

    Args:
        issue_key: e.g. 'KAN-3'.
        comment_id: The numeric comment ID.
        new_text: Replacement plain-text body for the comment.
    """
    h = _headers()
    cid = _cloud_id(h)
    r = requests.put(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}/comment/{comment_id}",
        headers=h,
        json={"body": _adf(new_text)},
        timeout=15,
    )
    if r.status_code >= 400:
        return {"error": r.status_code, "body": r.text}
    return {"updated": comment_id}


@tool(expected_credentials=JIRA_CONNECTIONS)
def jira_delete_issue_comment(issue_key: str, comment_id: str) -> dict:
    """Delete a comment from a Jira issue.

    Args:
        issue_key: e.g. 'KAN-3'.
        comment_id: The numeric comment ID.
    """
    h = _headers()
    cid = _cloud_id(h)
    r = requests.delete(
        f"https://api.atlassian.com/ex/jira/{cid}/rest/api/3/issue/{issue_key}/comment/{comment_id}",
        headers=h,
        timeout=15,
    )
    if r.status_code == 204:
        return {"deleted": comment_id}
    return {"error": r.status_code, "body": r.text}
