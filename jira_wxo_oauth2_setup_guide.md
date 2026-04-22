# Jira Connection Setup Guide

This guide walks through creating a Jira account, connecting it to watsonx Orchestrate (WXO) via OAuth 2.0, and configuring the **Issue Manager** (Jira) agent. You will need a throwaway email, a Jira free trial, your IBM Cloud region, and the Atlassian Developer Console.

**Two paths are covered for adding the Issue Manager agent:**

- **Path A (preferred):** Import from the WXO **Discover** catalog — all UI.
- **Path B (fallback):** Import via the **ADK CLI** using the files in [`issue_manager/`](./issue_manager/) — use this when the agent doesn't appear in Discover.

See [section 5](#5-jira-agent-configuration-in-wxo) for both paths. The rest of this guide (Atlassian OAuth app, WXO connection, agent behavior) applies regardless of which path you take.

---

## Before you start — prerequisites

Before working through this guide, set up a local development environment.

### Install VS Code

Download and install **Visual Studio Code** (free, macOS/Windows/Linux):

[https://code.visualstudio.com/download](https://code.visualstudio.com/download)

You will use VS Code as your editor and to run shell commands from its integrated terminal (`` Cmd+` `` on macOS, `` Ctrl+` `` on Windows/Linux).

### (Optional) Install Claude Code

If you want AI assistance navigating this guide or debugging errors, install **Claude Code**. It runs in your terminal and can read/edit files alongside you:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

See [claude.com/product/claude-code](https://www.claude.com/product/claude-code) for details. This is **optional** — every step below works without it.

### Clone or download this repository

The files you will use in Path B (the [`issue_manager/`](./issue_manager/) ADK export) and all the screenshots referenced in this guide live in the GitHub repo **[tbbates1/jira_setup](https://github.com/tbbates1/jira_setup)**. Pick one of the two options below.

**Option A — Clone with git (recommended):**

```bash
git clone https://github.com/tbbates1/jira_setup.git
cd jira_setup
```

**Option B — Download as a ZIP:**

1. Open [github.com/tbbates1/jira_setup](https://github.com/tbbates1/jira_setup) in your browser.
2. Click the green **Code** button → **Download ZIP**.
3. Unzip the downloaded file and open the resulting `jira_setup-main/` folder.

Open the folder in VS Code (`File → Open Folder…`), then use its integrated terminal to run the shell commands you will see in this guide.

---

### 1. Create an email account

You need an email address to create the Jira account. You can use your company email, but the Jira free trial expires after 30 days — so if you run this lab frequently, a throwaway email is better.

> **Tip:** Do all of this in a **Chrome Guest tab** so it doesn't interfere with your existing Outlook/Google accounts.

1. Go to [outlook.com](https://outlook.com) and click **Create free account**
2. Create a new email address (e.g. `mortgage-lab-1@outlook.com`)
3. Set a password and complete the signup

Save your email and password somewhere — you will need them for the Jira signup.

---

### 2. Create a Jira account

1. Go to [atlassian.com/software/jira](https://www.atlassian.com/software/jira) and sign up with your new email address
2. Verify your email
3. When prompted to name your space, enter **Mortgage Leads**
4. When asked what types of tasks you need, select **Task** and continue
5. Once setup is complete, configure the board columns to show **TO DO** and **DONE**

<img src="photos/14.png" alt="Mortgage Leads board" width="1000">

---

### 3. Create an OAuth 2.0 app in the Atlassian Developer Console

1. Go to [developer.atlassian.com](https://developer.atlassian.com) and log in with the same Atlassian account you used to create your Jira instance
2. Click your profile icon in the top right and select **Developer console**
3. Navigate to [developer.atlassian.com/console/myapps](https://developer.atlassian.com/console/myapps/)
4. Click **Create** and select **OAuth 2.0 integration**
5. Name the app (e.g. `wxo-mortgage-lab`), accept the terms, and click **Create**

#### 3.1 Permissions

6. In the left sidebar, click **Permissions**
7. Find **Jira API** in the list and click **Add** (it will change to **Configure**)
8. Click **Configure** next to Jira API, then click **Edit Scopes** under **Jira platform REST API**
9. Enable these three scopes:

| Scope | Code | Purpose |
|-------|------|---------|
| View Jira issue data | `read:jira-work` | Read projects, issues, attachments |
| Create and manage issues | `write:jira-work` | Create/edit issues, post comments |
| View user profiles | `read:jira-user` | Resolve usernames and assignees |

10. Click **Save**. You do **not** need the Jira Service Management scopes.

#### 3.2 Get Client ID and Secret

11. In the left sidebar, click **Settings**
12. Under **Authentication details**, copy the **Client ID**
13. Click the refresh icon next to **Secret** to generate a secret, then copy it

<img src="photos/23.png" alt="Settings page — Client ID and Secret" width="1000">

Keep both values — you will need them in the next step.

#### 3.3 Authorization (Callback URL)

14. In the left sidebar, click **Authorization**
15. Next to **OAuth 2.0 (3LO)**, click **Add**
16. Paste your callback URL into the **Callback URLs** field and click **Save changes**

<img src="photos/24.png" alt="Authorization page with callback URL" width="1000">

The callback URL follows this pattern — replace `<region>` with your WXO region (e.g. `us-south`, `eu-de`):

```
https://<region>.watson-orchestrate.cloud.ibm.com/mfe_connectors/api/v1/agentic/oauth/_callback
```

You can find your region from the WXO URL in your browser (e.g. `us-south.watson-orchestrate.cloud.ibm.com/manage/connectors` means your region is `us-south`).

> **Tip: Don't know your region?** You can skip this step for now, fill in the WXO connection form (step 4), and attempt to authenticate. The authentication will fail with an error like (look at the url):
>
> ```
> redirect_uri is not registered for client: https://us-south.watson-orchestrate.cloud.ibm.com/mfe_connectors/api/v1/agentic/oauth/_callback
> ```
>
> <img src="photos/22.png" alt="Atlassian callback URL error" width="1000">
>
> The URL after `redirect_uri is not registered for client:` is your callback URL. Copy it, come back to this step, and add it.

#### 3.4 Distribution (enable sharing)

By default, new OAuth apps are **private** — only you can use them. You need to enable sharing so WXO can access the app.

17. In the left sidebar, click **Distribution**
18. Click **Edit distribution controls**
19. Set **Distribution status** to **Sharing**
20. Fill in the required fields:

| Field | Value |
|-------|-------|
| **Vendor name** | `IBM` (or your company name) |
| **Privacy policy** | `https://www.ibm.com/` |
| **Does your app store personal data?** | No |

21. Click **Save changes**

> If you skip this step, you will see a **"You don't have access to this app"** error when WXO tries to authenticate with Jira.

---

### 4. Launch watsonx Orchestrate and set up the connection

1. Go to [cloud.ibm.com/resources](https://cloud.ibm.com/resources)
2. Under **AI / Machine Learning**, find your **Watson Orchestrate** instance and click on it

<img src="photos/17.png" alt="IBM Cloud Resource list" width="600">

3. Click **Launch watsonx Orchestrate**

<img src="photos/18.png" alt="Watson Orchestrate launch page" width="600">

4. In WXO, click the hamburger menu, go to **Manage** > **Connections**

<img src="photos/20.png" alt="WXO sidebar — Manage > Connections" width="600">

5. Search for **jira** and click the edit icon next to the **Jira** connection (`jira_oauth2_auth_code_ibm_...`)

<img src="photos/21.png" alt="WXO Connections list — Jira" width="600">

6. Fill in the following fields:

| Field | Value |
|-------|-------|
| **Authentication type** | Oauth2 Authorization Code |
| **Server URL** | `https://api.atlassian.com` |
| **Token URL** | `https://auth.atlassian.com/oauth/token` |
| **Authorization URL** | `https://auth.atlassian.com/authorize` |
| **Client ID** | *(from step 3.2)* |
| **Client Secret** | *(from step 3.2)* |
| **Scope** | `read:jira-work write:jira-work read:jira-user offline_access` |
| **Credential type** | Team credentials |

#### 4.1 Auth Request Fields

Under **Auth request field**, click "Add field" and add these two entries:

| Key | Value |
|-----|-------|
| `audience` | `api.atlassian.com` |
| `prompt` | `consent` |

The `audience` parameter is required for Jira Cloud OAuth 2.0 (3LO) to work correctly.

#### 4.2 Important Notes

- **Server URL must be `https://api.atlassian.com`** — not your Jira instance URL. The WXO Jira tools call the Atlassian API at `api.atlassian.com/oauth/token/accessible-resources` to discover your Jira site. Using your instance URL (e.g., `https://yoursite.atlassian.net`) will result in a 404 error.
- **`offline_access` scope** gives you a refresh token so the connection doesn't expire after one hour.

7. Click **Save changes**, then click **Continue** when prompted to authenticate

8. You will be redirected to Atlassian. The app will request access to your Jira account — click **Accept**

> **Optional:** You can also set up the **Live** connection with the same settings. Click the **Live** tab on the connection and repeat the same configuration. The Draft connection is enough for testing, but Live is needed if you want to publish the agent.

---

### 5. JIRA Agent Configuration in WXO

There are **two ways** to add the Issue Manager agent to your WXO instance:

- **Path A — Import from Discover catalog** (preferred, UI-only). Use this when the **Issue Manager** agent is visible in **Build → Discover**.
- **Path B — Import via the ADK CLI** (fallback). Use this when the agent does **not** appear in Discover. A complete ADK export of the agent is included in this repo at [`issue_manager/`](./issue_manager/).

> **Why two paths?** The Discover catalog content varies by region, account type, and WXO version. If you can't find the **Issue Manager** tile in Discover, don't worry — Path B gives you the same agent via the ADK.
>
> Note: WXO does **not** support uploading a `.zip` through the Discover UI. External agents must be imported via the ADK CLI.

Pick **one** path below, then continue to step 5.2.

---

#### 5.1 Path A — Import from Discover catalog

1. In WXO, go to **Build** and click **Discover** to open the catalog

<img src="photos/79.png" alt="WXO Build page — click Discover" width="600">

<img src="photos/81.png" alt="WXO Discover catalog" width="600">

2. Search for **Issue Manager** and click on the **Issue Manager** agent (the Jira one, by IBM)

<img src="photos/82.png" alt="Search results for Issue Manager" width="600">

3. Click **Use as template**

<img src="photos/83.png" alt="Issue Manager agent detail page" width="600">

4. You will be taken to the agent editor

<img src="photos/84.png" alt="Issue Manager agent editor" width="600">

> **Can't find the Issue Manager agent in Discover?** Skip this section and use **Path B** below.

---

#### 5.1-ALT Path B — Import via the ADK CLI (fallback)

Use this path when the Issue Manager agent is **not** visible in the WXO **Discover** catalog. You will use the **watsonx Orchestrate ADK CLI** to import the agent YAML from the [`issue_manager/`](./issue_manager/) folder in this repo.

If this is your first time using the ADK, don't worry — the sub-steps below walk through every step from scratch (getting your WXO credentials, installing Python, creating a virtual environment, installing the ADK CLI, connecting it to your WXO instance, and importing the agent). No prior ADK experience is required.

> **Official reference docs (external):**
> - [Installing the ADK](https://developer.watson-orchestrate.ibm.com/getting_started/installing)
> - [Importing an agent](https://developer.watson-orchestrate.ibm.com/agents/import_agent)

---

##### Step 1 — Get your WXO credentials

You need **two values** from your watsonx Orchestrate instance:

1. **Service instance URL** — looks like `https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>`
2. **API key**

How to get them:

1. Open watsonx Orchestrate in your browser.
2. Click your **profile icon** (top right) → **Settings**.
3. Go to the **API details** tab.
4. **Copy** the **Service instance URL** and save it somewhere.
5. Click **Generate API key** — you will be taken to IBM Cloud's API keys page.
6. On that page, click **Create**, then **copy the key immediately** and save it somewhere safe. You will not be able to view it again.

Keep both values handy — you will paste them below.

---

##### Step 2 — Install Python 3.11, 3.12, or 3.13

The ADK CLI requires Python **3.11, 3.12, or 3.13**. Check what you have installed:

```bash
python3 --version
```

If the version is not one of those three (for example, you see 3.10 or 3.14), install a supported version. On macOS with [Homebrew](https://brew.sh):

```bash
brew install python@3.11
```

> You can use `python@3.12` or `python@3.13` instead — any of the three works. Replace `python3.11` with your chosen version in the rest of these commands.

---

##### Step 3 — Create and activate a Python virtual environment

A virtual environment keeps the ADK's Python packages isolated from your system Python.

From the root of this repo (the folder **containing** `jira_setup_ai_challenge/`), create a venv:

```bash
python3.11 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Your terminal prompt should now start with `(.venv)`. Confirm the Python version inside the venv:

```bash
python3 --version
```

Keep this venv active for the rest of this guide. If you open a new terminal later, re-activate it with `source .venv/bin/activate`.

---

##### Step 4 — Install the ADK CLI

With the venv active, install the watsonx Orchestrate ADK:

```bash
pip install ibm-watsonx-orchestrate
```

Verify the install:

```bash
orchestrate --version
```

You should see a version number printed.

---

##### Step 5 — Register your WXO environment with the ADK

The ADK uses named **environments** to know which WXO instance to talk to. You can name your environment **anything you want** — `jira_setup`, `my_wxo`, `work`, `demo`, whatever you will remember. The name is just a local label; it has no effect on WXO itself.

Pick a name, then run the command below. Replace:
- `<your-env-name>` with the name you picked
- `<your-service-instance-url>` with the Service instance URL from Step 1

```bash
orchestrate env add -n <your-env-name> -u <your-service-instance-url>
```

**Concrete example** (env name `jira_setup` and a sample URL):

```bash
orchestrate env add -n jira_setup -u https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/abc123-your-instance-id
```

You should see:

```
[INFO] - Environment '<your-env-name>' has been created
```

> **Already registered a WXO environment before?** Run `orchestrate env list` to see what's already registered. You can reuse an existing name — just skip this step and use that name in Step 6.

---

##### Step 6 — Activate the environment

Activate the environment you just registered (use the same name):

```bash
orchestrate env activate <your-env-name>
```

For example:

```bash
orchestrate env activate jira_setup
```

When prompted, paste the **API key** from Step 1:

```
Please enter WXO API key:
```

You should see:

```
[INFO] - Environment '<your-env-name>' is now active
```

Your ADK CLI is now connected to your WXO instance.

---

##### Step 7 — Import the Issue Manager agent

Navigate into the `jira_setup_ai_challenge` directory:

```bash
cd jira_setup_ai_challenge
```

Import the agent YAML:

```bash
orchestrate agents import -f issue_manager/agents/native/jira_issue_management_agent_41df14f2.yaml
```

The Issue Manager agent uses **IBM out-of-the-box (OOTB) tools** (`create_an_issue`, `get_projects`, `get_project_issue_types`, etc.) that are normally pre-registered in every WXO instance. In most cases, importing the agent YAML alone is enough.

- **If the command succeeds** → skip to [Step 9 — Verify](#step-9--verify-the-import).
- **If the command fails** with "tool not found" or "connection not found" → continue with Step 8.

---

##### Step 8 — (Only if Step 7 failed) Import the tools and connection

Run this step only if Step 7 reported missing tools or a missing connection. It imports every tool and the Jira connection spec from the [`issue_manager/`](./issue_manager/) folder.

First, import the Jira connection spec:

```bash
orchestrate connections import -f issue_manager/connections/jira_ibm_184bdbd3.yaml
```

Then import each tool. Every tool lives in its own folder under `issue_manager/tools/`:

```bash
orchestrate tools import -k python -f issue_manager/tools/create_an_issue_9b358
orchestrate tools import -k python -f issue_manager/tools/delete_an_issue_6095b
orchestrate tools import -k python -f issue_manager/tools/delete_an_issue_comment_9329c
orchestrate tools import -k python -f issue_manager/tools/get_issue_priorities_11025
orchestrate tools import -k python -f issue_manager/tools/get_issues_b8d23
orchestrate tools import -k python -f issue_manager/tools/get_project_issue_types_f6753
orchestrate tools import -k python -f issue_manager/tools/get_projects_52926
orchestrate tools import -k python -f issue_manager/tools/get_users_49c26
orchestrate tools import -k python -f issue_manager/tools/update_an_issue_a9c66
orchestrate tools import -k python -f issue_manager/tools/update_issue_comment_c6ec1
```

Then re-run the agent import from Step 7:

```bash
orchestrate agents import -f issue_manager/agents/native/jira_issue_management_agent_41df14f2.yaml
```

> **Import command errors out on the package folder?** If `orchestrate tools import` complains that it expects a `.py` file rather than a directory, your ADK version may not accept this OOTB package layout. Options: upgrade the ADK (`pip install -U ibm-watsonx-orchestrate`), or ask your instructor for a packaged `.py` version of the tools.

---

##### Step 9 — Verify the import

List your agents:

```bash
orchestrate agents list
```

You should see `jira_issue_management_agent_41df14f2` (display name: **Issue Manager**) in the output.

Refresh the WXO UI in your browser and go to **Build** — the **Issue Manager** agent should now appear.

---

##### Step 10 — Rename with your initials (optional but recommended)

If multiple people share the same WXO instance, rename the agent so it does not collide with others'.

**Option A — in the WXO UI:**
1. Go to **Build** and open your imported **Issue Manager** agent.
2. Click the pencil icon next to the agent name and update it (e.g. **Issue Manager TB**).

**Option B — before importing, edit the YAML:**
Open `issue_manager/agents/native/jira_issue_management_agent_41df14f2.yaml` and change:
- `name:` → something unique, e.g. `jira_issue_management_agent_TB`
- `display_name:` → e.g. `Issue Manager TB`

Then re-run `orchestrate agents import -f …` from Step 7.

---

**Regardless of which path (A or B) you took, you still need to:**
- Complete the WXO Jira connection setup in [section 4](#4-launch-watsonx-orchestrate-and-set-up-the-connection).
- Update the agent's behavior instructions in [section 5.3](#53-update-behavior-instructions) so it knows your Jira `project_id` and `issuetype_id`.

#### 5.2 Get Project and Issue Type IDs

The JIRA agent comes with pre-built tools to query Jira. Use the agent preview chat (click **Talk to agent**) to discover your IDs:

**Step 1** — In the agent preview, type:
```
Get projects in Jira
```
Note the `project_id` for your target project (e.g., `mortgage_lab` = `10001`).

**Step 2** — Then type:
```
Get project issue types for project_id: <your_project_id>
```
Note the `issuetype_id` for the **Task** type (e.g., `Task` = `10005`).

<img src="photos/25.png" alt="Agent preview showing project ID and issue type ID" width="600">

#### 5.3 Update Behavior Instructions

Go to **Behavior** in the left sidebar. Replace the default instructions with the text below.

> **Important:** Before pasting, update the two highlighted values to match your Jira instance:
> - **`project_id: "XXXXX"`** — replace with your project ID from step 2
> - **`issuetype_id: "XXXXX"`** — replace with your Task issue type ID from step 2
>
> Do **not** add the behavior text to the agent yet — just prepare it with your correct values. You will paste it in the next step.

```
## Role
You will be given a meeting summary with customer details. Use that as the description of the JIRA issue.

CRITICAL: The meeting summary should contain actual customer data, NOT placeholders.
- If you receive placeholders like "[Name]" or "[amount if known]", this indicates an error in the workflow
- The Meeting Helper should have already filled in all actual values before sending to you

When creating JIRA issues:
- Use description: The complete meeting summary provided (should contain actual customer details)
- Use project_id: "10001"
- Use issuetype_id: "10005"
- Use summary: Extract the customer name if provided, or use a brief descriptive title

Expected description format (with actual values filled in):
Customer Name: [Actual name]
First-time buyer: [Yes/No/Not specified]
Monthly Income (post-tax): [Actual amount]
Potential Deposit: [Actual amount]
Mortgage Affordability: [Actual details or "Not calculated"]
Branch: [Branch name]
Date: [Date in YYYY-MM-DD format]
Time: [Time]
Adviser: [Adviser name]

Response guidelines:
- Create the JIRA issue immediately with the provided details
- Respond with a brief acknowledgment like "Thanks!" or "Great!"
- Do not ask the user for additional information
```

#### 5.4 Test the Agent

Send this message in the agent preview to verify everything works:

```
Create a Jira issue with summary "Test mortgage lead" and description "Customer Name: Anna Müller, First-time buyer: Yes, Monthly Income: CHF 8,500, Potential Deposit: CHF 50,000, Mortgage Affordability: CHF 425,000, Branch: Zürich, Date: 2026-03-18, Time: 14:00, Adviser: Marc Weber"
```

The agent should create the issue immediately without asking for project, issue type, or priority. Verify the ticket appears on your Jira board.

<img src="photos/26.png" alt="Issue Manager test — Jira issue created successfully" width="1000">

#### 5.5 Copy Behavior to the User Lab Instructions

The behavior instructions you configured above set default values for `project_id` and `issuetype_id` that the Issue Manager agent needs. These same defaults must be used in both the **ADK lab** and the **no-code lab** — each lab user creates its own Issue Manager XY agent, and each one needs this updated behavior.

The values `project_id: "10001"` and `issuetype_id: "10005"` are the Jira defaults for a new instance, so lab users can copy the behavior text from step 5.3 as-is. However, when setting up the lab from scratch, the instructor should verify these values match by running the commands in step 5.2. If the values differ, update the behavior text in the participant instructions (`adk_lab_user/instructions.md` and `no_code_agent_instructions/`) before the lab begins.

When setting up the Issue Manager agent in either lab, **do not use the default behavior** from the Discovery catalog. The catalog default does not include project-specific IDs, so the agent will ask the user to select a project and issue type every time. Instead, replace the behavior with the full text from step 5.3.

#### 5.6 Delete the Agent from WXO

Now that you have verified the Jira connection and behavior work correctly, **delete the Issue Manager agent** from watsonx Orchestrate. Each lab participant will add and configure the agent themselves as part of the lab exercise.

1. Go to **Build** > **Manage agents**
2. Click on the **Issue Manager** agent
3. Click the **three-dot menu** (top right) and select **Delete**

<img src="photos/26.png" alt="Deleting the Issue Manager agent from WXO" width="1000">

4. Also delete the **AskOrchestrate** agent that comes pre-installed — it may distract lab participants. Delete it the same way.

The WXO instance should now have **no agents** on the Build page, giving lab participants a clean starting point.

---

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Issue Manager agent not visible in **Discover** | Catalog content varies by region / account / WXO version | Use **Path B** in section 5.1-ALT to import the agent via the ADK CLI from the [`issue_manager/`](./issue_manager/) folder |
| Tried to upload a `.zip` in Discover, no option to do so | WXO Discover does not support `.zip` uploads | Import via the ADK CLI instead — see section 5.1-ALT |
| `redirect_uri is not registered for client` | Callback URL not added in Atlassian Developer Console | Add the WXO callback URL under **Authorization** in your Atlassian app |
| `Caught error during Jira client initialization: base_url` | Server URL is blank in WXO connection | Set Server URL to `https://api.atlassian.com` |
| `404 Not Found for url: https://yoursite.atlassian.net/oauth/token/accessible-resources` | Server URL is set to your Jira instance instead of the API | Change Server URL to `https://api.atlassian.com` |
| Agent asks for project/issue type/priority each time | Default behavior instructions not updated | Replace behavior instructions with the updated version above |
| `unauthorized_client` | OAuth app permissions or callback URL misconfigured | Check scopes in Permissions tab and callback URL in Authorization tab |
