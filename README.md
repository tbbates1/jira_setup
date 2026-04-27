# jira_setup

A from-scratch starting point for building a **custom Jira agent in watsonx Orchestrate (WXO)** — your own OAuth2 connection, your own Python tools, your own agent. No prebuilt templates.

## Contents

- [`jira_wxo_oauth2_setup_guide.md`](./jira_wxo_oauth2_setup_guide.md) — full step-by-step setup instructions
- [`jira_agent/`](./jira_agent/) — the agent and tool source files:
  - [`jira_tools.py`](./jira_agent/jira_tools.py) — 10 Python tools covering full CRUD on projects, issues, and comments
  - [`agent.yaml`](./jira_agent/agent.yaml) — the agent definition
  - [`requirements.txt`](./jira_agent/requirements.txt) — Python deps
- [`photos/`](./photos/) — screenshots referenced in the guide

## What this gives you

A working baseline that proves the end-to-end path:

- Atlassian OAuth 2.0 app → custom WXO connection → Python tools → custom agent → tested via the WXO API.

The guide walks through creating the Jira account, the Atlassian OAuth app, the WXO connection (via the ADK CLI), and importing the tools and agent.

## This is a starting point — tune it for your use case

Out-of-the-box this is a **generic** Jira agent. To get good performance for *your* workflow, you should:

- **Trim the tools.** Each `@tool` you import expands the LLM's tool surface. Only import the subset of [`jira_tools.py`](./jira_agent/jira_tools.py) your agent actually needs (e.g. drop create/update/delete if you only ever read).
- **Customize the behavior.** The `instructions:` block in [`agent.yaml`](./jira_agent/agent.yaml) is generic. Real performance comes from rewriting it to describe *your* projects, defaults, conventions, and refusal rules.
- **Add tools you don't see here.** The baseline covers projects, issues, and comments. If you need attachments, transitions, sprints, custom fields, etc., write a new `@tool` following the same pattern and import it.
- **Iterate.** Run real prompts, watch where it picks the wrong tool, and tighten the docstrings — they *are* the LLM's reference manual.

The repo gives you the plumbing. The performance comes from what you build on top.

## Getting started

1. Install **VS Code**: https://code.visualstudio.com/download
2. Clone this repo:
   ```bash
   git clone https://github.com/tbbates1/jira_setup.git
   cd jira_setup
   ```
3. Open [`jira_wxo_oauth2_setup_guide.md`](./jira_wxo_oauth2_setup_guide.md) and follow the steps.
