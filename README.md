# jira_setup

Everything you need to connect **Jira** to **watsonx Orchestrate (WXO)** via OAuth 2.0 and get the **Issue Manager** (Jira) agent running.

This is the self-contained reference for the lab's Jira portion — it covers the Atlassian + WXO connection setup **and** a fallback path for when the Issue Manager agent is not visible in the WXO Discover catalog.

## Contents

- [jira_wxo_oauth2_setup_guide.md](./jira_wxo_oauth2_setup_guide.md) — Step-by-step setup instructions (prerequisites, Atlassian OAuth app, WXO connection, agent behavior, ADK import fallback, troubleshooting)
- [issue_manager/](./issue_manager/) — Full ADK export of the Issue Manager agent (used as a fallback when the agent doesn't appear in Discover)
- [photos/](./photos/) — Screenshots referenced in the guide

## Getting started

1. Install **VS Code**: https://code.visualstudio.com/download
2. *(Optional)* Install **Claude Code**: `curl -fsSL https://claude.ai/install.sh | bash`
3. Clone this repo:
   ```bash
   git clone https://github.com/tbbates1/jira_setup.git
   cd jira_setup
   ```
   Or download as a ZIP from the green **Code** button on [github.com/tbbates1/jira_setup](https://github.com/tbbates1/jira_setup).
4. Open `jira_wxo_oauth2_setup_guide.md` and follow the steps.

## What this covers

1. Creating a Jira account and project
2. Setting up an OAuth 2.0 app in the Atlassian Developer Console
3. Connecting Jira to watsonx Orchestrate
4. Configuring the Issue Manager agent in WXO — two paths:
   - **Path A (preferred):** Import from the WXO **Discover** catalog
   - **Path B (fallback):** Import via the **ADK CLI** using the files in [`issue_manager/`](./issue_manager/) — use this when the Issue Manager agent does not appear in Discover
5. Updating the agent's behavior (project_id / issuetype_id defaults)
6. Troubleshooting common issues

## When to use the ADK fallback (Path B)

Sometimes the **Issue Manager** agent does **not** appear in the WXO **Build → Discover** catalog (catalog content varies by region / account / WXO version). If that happens, you have three options:

1. **Use the ADK CLI** to import the agent directly from the [`issue_manager/`](./issue_manager/) folder in this repo — this is the recommended fallback. See the "ADK Import Fallback" section in [jira_wxo_oauth2_setup_guide.md](./jira_wxo_oauth2_setup_guide.md).
2. **Download** the [`issue_manager/`](./issue_manager/) folder (or clone this repo) and customize the YAML/behavior before importing.
3. **Edit in the WXO UI** after importing — behavior, tools, and collaborators can all be changed in the Build page.

> **Note:** WXO does not currently support uploading an agent as a `.zip` through the Discover UI — the ADK CLI is the path for importing externally-provided agents. See the ADK docs:
> - [Getting started / installing](https://developer.watson-orchestrate.ibm.com/getting_started/installing)
> - [Import an agent](https://developer.watson-orchestrate.ibm.com/agents/import_agent)
