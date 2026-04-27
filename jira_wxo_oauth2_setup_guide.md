# Custom Jira Agent for watsonx Orchestrate — Setup Guide

End-to-end instructions for building a **custom Jira agent in watsonx Orchestrate (WXO)** from scratch:

- Create a Jira instance and an Atlassian OAuth 2.0 app.
- Create a **custom OAuth2 connection** in WXO.
- Import **10 custom Python tools** that cover full CRUD on Jira projects, issues, and comments.
- Import a **custom agent** wired to those tools.
- Authenticate the connection in the WXO UI.
- Test end-to-end via the WXO REST API.

Everything lives in this repo:

- [`jira_agent/jira_tools.py`](./jira_agent/jira_tools.py) — the 10 Python tools
- [`jira_agent/agent.yaml`](./jira_agent/agent.yaml) — the agent definition
- [`jira_agent/requirements.txt`](./jira_agent/requirements.txt) — Python deps for the tools

---

## Treat this as a starting point, not a finished product

**Important:** what's in this repo is a **clean, working baseline** — enough to verify connectivity end-to-end and understand the moving parts. It is **not** tuned for any specific use case.

To get the agent performing well for *your* workflow, you should:

- **Trim the tools.** Each `@tool` you import increases the LLM's context and broadens the surface for tool-selection mistakes. Only import the subset of [`jira_tools.py`](./jira_agent/jira_tools.py) your agent actually needs. If you only ever read issues, delete the create/update/delete functions before importing. If you never touch comments, drop the comment tools.
- **Customize the behavior.** The `instructions:` block in [`agent.yaml`](./jira_agent/agent.yaml) is generic. Real performance comes from making it *your* behavior — describe your project IDs, your default issue types, your team's conventions, the exact workflows you want the agent to follow, and what to refuse. Anything you would tell a new teammate on day one belongs in there.
- **Add tools you don't see here.** This baseline covers projects, issues, and comments. If you need attachments, transitions, sprints, boards, custom fields, links, or anything else in the Jira REST API, write the `@tool` and import it — it's just a few lines on top of the pattern shown.
- **Iterate on prompts.** Run the agent against real prompts, watch where it picks the wrong tool or asks for too much, and tighten the docstrings and instructions. The docstrings *are* the LLM's reference manual; small wording changes there often beat large code changes.

The repo gives you the plumbing. The performance comes from what you do on top.

---

## 0 · Prerequisites

### 0.1 Python 3.11, 3.12, or 3.13

The watsonx Orchestrate ADK CLI requires one of these versions. Check what you have:

```bash
python3 --version
```

If you don't have a supported version, install one. On macOS with [Homebrew](https://brew.sh):

```bash
brew install python@3.11
```

### 0.2 Clone this repo

```bash
git clone https://github.com/tbbates1/jira_setup.git
cd jira_setup
```

Or download as a ZIP from the green **Code** button on [github.com/tbbates1/jira_setup](https://github.com/tbbates1/jira_setup).

### 0.3 Set up a virtual environment and install the ADK

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install ibm-watsonx-orchestrate
orchestrate --version
```

Keep this venv active for the rest of the guide. Re-activate with `source .venv/bin/activate` if you open a new terminal.

---

## 1 · Create a Jira account

1. Go to [atlassian.com/software/jira](https://www.atlassian.com/software/jira) and sign up.
2. Verify your email.
3. Create a workspace and a project (any template — Kanban or Scrum works fine).
4. Take note of the **project key** Atlassian assigns (e.g. `KAN`, `PROJ`). You will use it later.

> **Tip — use a throwaway, shareable account.** Sign up for Jira with a fresh email (e.g. an `outlook.com` account created in a Chrome Guest tab) instead of your work address. Two reasons:
>
> 1. **Avoid collisions** with any existing Atlassian login on your work email.
> 2. **Make it shareable across the team.** Atlassian (Jira + the Developer Console you'll use in §2) requires two-factor authentication on the account, which makes credential sharing painful. Outlook lets you create the email without 2FA, so you can hand the same login to teammates and they can authenticate the WXO connection in §5 without juggling phone-based 2FA codes.

---

## 2 · Create an OAuth 2.0 app in the Atlassian Developer Console

This is the Atlassian-side OAuth client your WXO connection will use.

1. Go to [developer.atlassian.com](https://developer.atlassian.com) and log in with the same Atlassian account you used to create your Jira instance.
2. Click your profile icon (top right) → **Developer console**.
3. Click **Create** → **OAuth 2.0 integration**, give it a name (e.g. `wxo-jira`), accept the terms, and click **Create**.

### 2.1 Permissions (scopes)

4. In the left sidebar, click **Permissions**.
5. Find **Jira API** in the list and click **Add** → then **Configure** → **Edit Scopes** under **Jira platform REST API**.
6. Enable these three scopes:

| Scope | Code | Purpose |
|---|---|---|
| View Jira issue data | `read:jira-work` | Read projects, issues, comments |
| Create and manage issues | `write:jira-work` | Create / update / delete issues, post comments |
| View user profiles | `read:jira-user` | Resolve usernames and assignees |

7. Click **Save**. (You do **not** need the Jira Service Management scopes.)

> The fourth scope WXO will request — `offline_access` — is **not** added in the Atlassian Permissions tab. It's an OAuth flow modifier; Atlassian grants it automatically when WXO requests it. You'll add it to WXO's scope string in §4.3.

### 2.2 Get the Client ID and Client Secret

8. In the left sidebar, click **Settings**.
9. Under **Authentication details**, copy the **Client ID**.
10. Click the refresh icon next to **Secret** to generate a secret, then copy it.

<img src="photos/23.png" alt="Settings page — Client ID and Secret" width="900">

Keep both values somewhere safe. You'll paste them into WXO in §4.3.

### 2.3 Add the WXO callback URL

11. In the left sidebar, click **Authorization** → next to **OAuth 2.0 (3LO)**, click **Add** (or **Configure**).
12. Paste your **callback URL** into the **Callback URLs** field and click **Save changes**.

<img src="photos/24.png" alt="Authorization page with callback URL" width="900">

The callback URL pattern is:

```
https://<region>.watson-orchestrate.cloud.ibm.com/mfe_connectors/api/v1/agentic/oauth/_callback
```

`<region>` matches the region of your WXO instance — e.g. `us-south`, `eu-de`. You can read it from your WXO browser URL once you launch the instance (§3).

> **Tip — don't know your region?** Skip this step for now. When you try to authenticate the WXO connection later (§5), Atlassian will fail with `redirect_uri is not registered for client: <full URL>`. Copy that URL, come back here, and add it.
>
> <img src="photos/22.png" alt="Atlassian callback URL error" width="900">

### 2.4 Distribution — enable sharing

By default a new OAuth app is **private**, so only you can use it. Switch it to sharing so WXO's connection-manager can complete the OAuth flow.

13. Sidebar → **Distribution** → **Edit distribution controls**.
14. Set **Distribution status** → **Sharing**.
15. Fill in the required fields:

| Field | Value |
|---|---|
| Vendor name | Your name or company |
| Privacy policy | Any URL (your company site is fine) |
| Does your app store personal data? | No |

16. Click **Save changes**.

> If you skip this step you'll see a **"You don't have access to this app"** error in the OAuth flow.

---

## 3 · Launch watsonx Orchestrate

1. Go to [cloud.ibm.com/resources](https://cloud.ibm.com/resources).
2. Under **AI / Machine Learning**, find your **Watson Orchestrate** instance and click it.

   <img src="photos/17.png" alt="IBM Cloud Resource list" width="600">

3. Click **Launch watsonx Orchestrate**.

   <img src="photos/18.png" alt="Watson Orchestrate launch page" width="600">

4. Note your region from the URL (`us-south.watson-orchestrate.cloud.ibm.com/...` → region is `us-south`). Update the Atlassian callback URL in §2.3 if you skipped it.

---

## 4 · Register your WXO instance with the ADK CLI

### 4.1 Get your WXO credentials

In the WXO UI:

1. Click your profile icon (top right) → **Settings** → **API details**.
2. Copy the **Service instance URL** — looks like `https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>`.
3. Click **Generate API key** — copy the key immediately (you won't see it again).

### 4.2 Activate the environment

Pick any name for the environment (it's just a local label):

```bash
orchestrate env add -n my_wxo -u <SERVICE_INSTANCE_URL>
orchestrate env activate my_wxo
```

When prompted for the API key, paste it. You'll see:

```
[INFO] - Environment 'my_wxo' is now active
```

### 4.3 Create the custom OAuth2 connection

This is the connection your tools will bind to. The `app_id` you choose here is the name your tools reference — keep it lowercase, alphanumeric, with underscores.

```bash
# Create the connection record
orchestrate connections add -a jira_lab

# Configure it: OAuth2 auth-code, team-shared (one token for all users)
orchestrate connections configure \
  -a jira_lab \
  --env draft \
  -t team \
  -k oauth_auth_code_flow \
  --server-url https://api.atlassian.com

# Set the OAuth client + endpoints + scopes (note offline_access for refresh tokens)
orchestrate connections set-credentials \
  -a jira_lab \
  --env draft \
  --client-id '<CLIENT_ID from §2.2>' \
  --client-secret '<CLIENT_SECRET from §2.2>' \
  --token-url 'https://auth.atlassian.com/oauth/token' \
  --auth-url 'https://auth.atlassian.com/authorize' \
  --scope 'read:jira-work write:jira-work read:jira-user offline_access' \
  --auth-entries audience=api.atlassian.com \
  --auth-entries prompt=consent
```

What each piece does:

- **`--server-url https://api.atlassian.com`** — base URL the tools will hit. Use the global Atlassian API host, **not** your `<site>.atlassian.net` URL. WXO's tools resolve the per-site cloud ID at runtime via `api.atlassian.com/oauth/token/accessible-resources`.
- **`--scope ... offline_access`** — `offline_access` is what gives you a **refresh token**. Without it, the access token expires after ~1 hour and the connection silently stops working.
- **`--auth-entries audience=api.atlassian.com`** — Atlassian OAuth 3LO requires this query parameter on the authorize and token requests.
- **`--auth-entries prompt=consent`** — forces the consent screen each time, so you always end up on the right Atlassian site picker.

> **Why a custom connection (and not a prebuilt template)?** Some prebuilt connection records on a WXO tenant are wired in a way that prevents credential injection into custom Python tools — you get an opaque `Error getting Python tool status` / `EOF` from the executor with no useful diagnostics. A connection you `orchestrate connections add` yourself avoids that pitfall entirely.

---

## 5 · Authenticate the connection in the WXO UI

Connection-add via CLI sets the *config* (URLs, scope, client id/secret) but not the *runtime token*. The runtime token comes from the OAuth consent flow, which has to happen in a browser.

1. In WXO, open the sidebar → **Manage** → **Connections**.

   <img src="photos/20.png" alt="WXO sidebar — Manage > Connections" width="600">

2. Search for the app id you used (`jira_lab`) → click it → click **Connect** / **Authenticate**.
3. You'll be redirected to Atlassian. Make sure you're signed in as the **Atlassian user who owns the Jira site you want to manage** — if you're signed in as the wrong user, sign out (or open a Chrome Guest window) before continuing.
4. Pick the site, click **Accept**.
5. Back in WXO, the connection should now show ✅ for the **Draft** environment.

> If Atlassian shows `id.atlassian.com/error?error=invalid_request`, the authorize request expired (you sat on the consent screen too long, or switched accounts mid-flow). Click **Authenticate** again from WXO to start a fresh flow.

---

## 6 · Import the tools and the agent

This is where the **starting-point** mindset matters. Before importing, **decide what your agent actually needs to do** and trim accordingly.

### 6.1 Decide what to import

[`jira_agent/jira_tools.py`](./jira_agent/jira_tools.py) defines ten `@tool`-decorated functions:

| Tool | When to keep it |
|---|---|
| `jira_get_projects` | Almost always — even if you hardcode a project, it's useful for discovery |
| `jira_get_project_issue_types` | Keep if you create issues; safe to drop if your agent only reads |
| `jira_get_issue_priorities` | Keep only if you actually use priorities |
| `jira_get_users` | Keep only if you assign issues |
| `jira_create_issue` | Drop if your agent is read-only |
| `jira_get_issues` | Almost always |
| `jira_update_issue` | Drop if your agent is read-only |
| `jira_delete_issue` | Drop unless deletion is genuinely part of the workflow (it's a high-blast-radius operation for an LLM) |
| `jira_update_issue_comment` | Drop unless your agent edits comments |
| `jira_delete_issue_comment` | Drop unless your agent deletes comments |

Open [`jira_agent/jira_tools.py`](./jira_agent/jira_tools.py) and **delete the `@tool` functions you don't need**, then update the `tools:` list in [`jira_agent/agent.yaml`](./jira_agent/agent.yaml) to match. Fewer tools = sharper LLM tool-selection and lower latency.

### 6.2 Customize the behavior

Open [`jira_agent/agent.yaml`](./jira_agent/agent.yaml) and rewrite the `instructions:` block to describe **your** workflow. Things worth specifying:

- The default project(s) the agent should operate in (so it doesn't have to ask every time).
- The default issue type for "create an issue" (e.g. always Task, unless the user says otherwise).
- Conventions for summary / description (length, format, what to include).
- What the agent should refuse (e.g. never delete issues without explicit confirmation).
- Whether to ask for assignee/priority or default to none.
- Output formatting (markdown table for >N items, plain prose otherwise, etc.).

The default `instructions` in the YAML covers the mechanical workflow — replace it with the product-specific behavior your use case needs.

### 6.3 Import

From the repo root, with your venv active:

```bash
orchestrate tools import \
  -k python \
  -f jira_agent/jira_tools.py \
  -r jira_agent/requirements.txt \
  -a jira_lab

orchestrate agents import -f jira_agent/agent.yaml
```

You should see `Tool '...' imported successfully` for each `@tool` you kept, and one `Agent '...' imported successfully` line.

If your connection's `app_id` differs from `jira_lab`, either:

- **Edit `jira_agent/jira_tools.py`** and change the `JIRA_APP_ID` constant near the top before importing, or
- **Use the remap form** of `-a`: `-a jira_lab=<your_app_id>` so the tool's reference (`jira_lab`) maps to your real connection at runtime.

> **Re-importing later:** if you change `jira_tools.py` after the agent already exists, re-import the tools **and** re-import the agent (`orchestrate agents remove -k native -n <agent_name>` then `orchestrate agents import -f agent.yaml`). Tool-id changes don't propagate to deployed agents automatically.

---

## 7 · Test the agent end-to-end

You can test in the WXO chat UI (Build → open your agent → **Talk to agent**), or via the WXO API. Below is an API test so the lab is reproducible from the terminal.

### 7.1 Find the agent ID

```bash
orchestrate agents list | grep <your_agent_name>
```

Copy the ID (a UUID).

### 7.2 Run a few prompts

Save the script below as `test_jira.py` and replace `AGENT_ID`:

```python
"""Smoke test for your Jira agent."""
import os
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watsonx_orchestrate_clients.chat.run_client import RunClient

API_KEY = os.environ["WXO_API_KEY"]
BASE_URL = os.environ["WXO_INSTANCE_URL"]  # https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>
AGENT_ID = "<paste agent UUID from `orchestrate agents list`>"

auth = IAMAuthenticator(apikey=API_KEY, url="https://iam.cloud.ibm.com/identity/token")
client = RunClient(base_url=BASE_URL, authenticator=auth)

PROMPTS = [
    "List all Jira projects.",
    "What are the issue types for project <YOUR_PROJECT_ID>?",
    "Create a Jira issue. project_id=<YOUR_PROJECT_ID>, issuetype_id=<YOUR_TASK_ISSUETYPE_ID>, "
        "summary='Hello from WXO', description='End-to-end smoke test.'",
    "List the issues in project <YOUR_PROJECT_KEY>.",
]

for p in PROMPTS:
    r = client.create_run(message=p, agent_id=AGENT_ID, capture_logs=True)
    final = client.wait_for_run_completion(r["run_id"], poll_interval=5, max_retries=72)
    msg = final.get("result", {}).get("data", {}).get("message", {})
    text = next((c["text"] for c in msg.get("content", []) if c.get("response_type") == "text"), None)
    print(f"\n>>> {p}\n{text}")
```

Run:

```bash
export WXO_API_KEY='<your API key>'
export WXO_INSTANCE_URL='https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>'
python test_jira.py
```

Suggested order:

1. **List projects** — confirms the OAuth token works and the `accessible-resources` lookup resolves your Atlassian site.
2. **Issue types for project X** — gets you the numeric `issuetype_id` for the **Task** type in your project (issue type IDs vary per Jira instance — don't hardcode).
3. **Create an issue** — uses the IDs from steps 1 and 2.
4. **List issues** — confirms the new issue is visible and that JQL search works.

You can also just chat in the WXO UI — the agent's instructions tell it to discover IDs itself if you don't supply them.

---

## 8 · What's in the toolkit (reference)

Each function below is a `@tool` in [`jira_agent/jira_tools.py`](./jira_agent/jira_tools.py). All are bound to the `jira_lab` connection and call Atlassian REST API v3 directly.

| Tool | Purpose |
|---|---|
| `jira_get_projects` | List or search projects |
| `jira_get_project_issue_types` | Issue types for a given project |
| `jira_get_issue_priorities` | Available priority values |
| `jira_get_users` | List or search users (for assignees) |
| `jira_create_issue` | Create an issue (project, type, summary, description, optional priority + assignee) |
| `jira_get_issues` | List issues in a project (JQL search), or fetch a single issue with comments |
| `jira_update_issue` | Update fields and/or add a comment |
| `jira_delete_issue` | Delete an issue |
| `jira_update_issue_comment` | Edit an existing comment |
| `jira_delete_issue_comment` | Delete a comment |

The OAuth bearer token is fetched via `connections.oauth2_auth_code("jira_lab")`, which the WXO runtime injects from the connection you authenticated in §5. To add a new tool, copy the pattern of any existing function and add it to the `tools:` list in `agent.yaml`.

---

## 9 · Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `redirect_uri is not registered for client` (Atlassian) | WXO callback URL not added in Atlassian Developer Console | Copy the URL from the Atlassian error and add it in §2.3 |
| `id.atlassian.com/error?error=invalid_request` | Stale authorize request — you sat on the consent screen too long or switched accounts | Click **Authenticate** in WXO again to get a fresh URL |
| `You don't have access to this app` (Atlassian) | OAuth app distribution status is **Private** | §2.4 — switch to **Sharing** |
| Tool returns `Error getting Python tool status` or `EOF` from executor | Connection app_id mismatch (most common) — the tool's `JIRA_APP_ID` doesn't match an authenticated connection on this tenant | Verify `orchestrate connections list` shows the app_id with ✅; either edit `JIRA_APP_ID` in `jira_tools.py` or use `-a <tool_app_id>=<wxo_app_id>` at import |
| `404` from `https://<site>.atlassian.net/...` in tool errors | `--server-url` was set to your Jira site instead of the API root | Reset `--server-url` to `https://api.atlassian.com` and re-run `orchestrate connections configure` |
| Agent says "I don't see any issues" but issues exist | `/search/jql` requires explicit `fields` since 2025 — already handled in `jira_tools.py`, but if you're authoring your own tools, pass `fields=summary,status` |
| Tool import fails with `No module named 'ibm_botocore'` | You're trying to import a tool with a private dependency that isn't on PyPI. Stick to the patterns in [`jira_agent/jira_tools.py`](./jira_agent/jira_tools.py) — only standard libraries plus `requests` |
| Token works briefly then stops working ~1 hour later | `offline_access` not in scope → no refresh token | Re-run `orchestrate connections set-credentials` with `--scope '... offline_access'` and re-authenticate in §5 |
| Mixing the OOTB Jira agent/tools with this custom setup — same `Error getting Python tool status` / `EOF` | Hybrids don't work. The OOTB Issue Manager and its tools hard-code `binding.python.connections.jira_ibm_<suffix>`, so they ignore your custom connection (`jira_lab`) entirely; conversely, this repo's tools won't pick up an OOTB connection's token if their `JIRA_APP_ID` doesn't match. Even a "correctly authenticated" OOTB connection can fail credential injection on some tenants with no useful error | Pick one path: either go fully custom (this guide), or fully OOTB. Don't try to half-import the OOTB Issue Manager and bolt the custom tools on top — they'll fight over which connection is "the" Jira connection and you'll burn hours chasing an opaque executor error. If you've already started down both paths, delete the OOTB agent + its 10 tools (`orchestrate agents remove -k native -n jira_issue_management_agent_*`, `orchestrate tools remove -n create_an_issue` etc.) before importing this repo's `jira_agent/` |

For more detail on connection internals see the official docs:

- [Build connections](https://developer.watson-orchestrate.ibm.com/connections/build_connections)
- [Associate Python connections to tools](https://developer.watson-orchestrate.ibm.com/connections/associate_connection_to_tool/python_connections)
- [Create a Python tool](https://developer.watson-orchestrate.ibm.com/tools/create_tool)
