# Example: Connecting Devin (Cognition) to Databricks Through Unity Gateway

This example applies the general pattern in the [Unity Gateway README](../../README.md) to Devin, Cognition's AI software engineer. It covers the two directions you are likely to need:

* **Databricks to Devin:** call the Devin and DeepWiki MCP servers from Genie Code or an agent, governed as Unity Gateway MCP Services.
* **Devin to Databricks:** let Devin sessions read from and act on a workspace, with the right identity and secret handling on the Devin side.

It also covers the Devin CLI, which helps with setup and testing.

> Findings below were tested in November 2026. Devin's product changes quickly; check the linked Devin docs before relying on any detail.

## Connection Details

| Server | URL | Transport | Auth |
| --- | --- | --- | --- |
| Devin MCP | `https://mcp.devin.ai/mcp` | Streamable HTTP | `Authorization: Bearer <cog_ key>` |
| DeepWiki MCP (public) | `https://mcp.deepwiki.com/mcp` (legacy SSE at `/sse`) | Streamable HTTP | None; public repositories only |

Devin key types ([Devin MCP](https://docs.devin.ai/work-with-devin/devin-mcp)):

| Key | Prefix | Extra header | Use for |
| --- | --- | --- | --- |
| Organization service user key | `cog_` | None (organization resolved from the key) | Shared, automated access. Recommended for a Unity Gateway service. |
| Enterprise service user key | `cog_` | `X-Org-Id: <org-id>` | Enterprise-wide automation |
| Personal access token | `cog_` | `X-Org-Id: <org-id>` | Personal, local tools (for example the Devin CLI) |
| Legacy API key | `apk_` / `apk_user_` | n/a | Repository documentation tools only. Session, playbook, knowledge, schedule and integration tools reject them. |

## What the Devin MCP Server Offers

Roughly 28 tools when tested, in four groups:

| Group | Examples | Risk |
| --- | --- | --- |
| Codebase Q&A | `ask_wiki_question`, `read_wiki_structure`, `read_wiki_contents`, `list_wiki_repos`, `generate_wiki` | Read (except `generate_wiki`, which starts indexing) |
| Sessions | `devin_session_create`, `devin_session_interact`, `devin_session_search`, `devin_session_events`, `devin_session_gather`, `devin_session_insights` | Create and message sessions that write code and open pull requests |
| Automation and review | `devin_automation_manage`, `devin_oncall_manage`, `devin_code_scan_manage`, `devin_review_manage`, `devin_schedule_manage` | Create event-driven or scheduled work; launch scans and fixes |
| Configuration and admin | `devin_knowledge_manage`, `devin_playbook_manage`, `devin_blueprint_test`, `devin_mcp_server_manage`, `devin_billing_tag_manage`, `devin_user_list`, `devin_find_setting`, `devin_list_integrations` | Change organization configuration |

Most management tools are **action-based**: one tool name covers both reads (`list`, `get`) and writes (`create`, `update`, `delete`). Tool selectors work on names, so they cannot split a tool's read actions from its write actions. Control that with the Devin key's role (a service user with only the permissions the workload needs) and with Unity Gateway service policies.

## Databricks to Devin: Registering the MCP Servers

Follow the README's steps with these choices:

1. **Connection.** Bearer token connection to `https://mcp.devin.ai` with base path `/mcp`, using an **organization service user key**. Every caller shares the service user's identity in Devin, so give the service user only the Devin permissions the callers need. Avoid personal access tokens and enterprise keys here; they also need the `X-Org-Id` header.
2. **Tool selection.** Start with the read tools (`ask_wiki_question`, `read_wiki_*`, `list_wiki_repos`, `devin_session_search`, `devin_find_setting`, `devin_list_integrations`). Add `devin_session_*` only when callers should start or steer Devin work, and add a service policy that requires approval for `devin_session_create`.
3. **DeepWiki.** For public repositories only, register `https://mcp.deepwiki.com/mcp` as a separate service with no authentication. It cannot see private repositories.
4. **Grant** `EXECUTE` on each service to the groups that need it. Never grant `USE CONNECTION`.

## Devin to Databricks: Identity and Repository Access

### Workspace identity

* Use a **dedicated Databricks service principal** for Devin, authenticated with OAuth machine-to-machine (`DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`): [Authorize service principal access with OAuth](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m/). Do not give Devin a personal access token.
* Grant only what the workload needs (for example `CAN_VIEW` or `CAN_MANAGE_RUN` on specific jobs and `CAN_READ` on specific folders). Runs that Devin starts or repairs still execute as the job's own `run_as` identity.
* Allow the workspace hostname in the Devin automation's or session's network policy. The OAuth token endpoint is on the same host. If the workspace uses IP access lists, confirm Devin's egress addresses with Cognition first.

### Repository access

* Devin sessions can **clone public repositories** without any setup.
* To **push branches and open pull requests**, install the Devin GitHub App on the GitHub organization with **Only select repositories**, then make the repository available to the Devin organization ([Devin GitHub integration](https://docs.devin.ai/integrations/gh)). Without it, pushes fail with HTTP 403 from Devin's Git proxy.
* The app requests broad permissions (read and write on contents, pull requests, workflows, actions and issues; read on organization administration and members). Scope it to the repositories Devin works on and protect the default branch so Devin can only open pull requests.
* Installing the app needs a GitHub organization owner (members can request it: [Requesting a GitHub App from your organization owner](https://docs.github.com/en/apps/using-github-apps/requesting-a-github-app-from-your-organization-owner)). In Devin Enterprise, an enterprise admin also assigns the repository to each Devin organization.

## Secret Management in Devin

Devin stores secrets at four scopes and loads them into the session VM as environment variables when a session starts. Values are shown as `[REDACTED SECRET]` in the UI ([VPC overview](https://docs.devin.ai/de/enterprise/vpc/overview)).

| Scope | Where | Who gets it |
| --- | --- | --- |
| Organization | **Settings > Secrets > Organization** | Every session in the Devin organization |
| Personal | **Settings > Secrets > Personal** | Only your own sessions, or a Devin service user you manage |
| Repository (blueprint) | The **Secrets** tab of a repository's blueprint | Sessions that use that repository's environment |
| Session | Entered in the web app when Devin asks for it mid-session | That session only |

Recommendations for Databricks credentials:

* **Do not use organization secrets** in a Devin organization shared by several teams: every session in that organization can read them. Expect to find other teams' credentials already in the environment, and have the first step of every task check `databricks current-user me` and stop if the identity is not the expected principal.
* **Prefer personal secrets on a Devin service user you manage.** The credentials then belong to the workload's own Devin identity, not to a person, and do not leak to other sessions.
* **For automations,** choose the run identity deliberately. Running as **creator** attributes sessions to you; running as **organization** uses the organization's system user, which does not get anyone's personal secrets.
* **Never paste secret values into a prompt or chat.** Use Devin's secret request flow or the settings pages. Never put values in links or MCP install payloads.
* **Rotate** the Databricks OAuth secret on a schedule and record its expiry.

Not yet verified (test before relying on it): whether sessions an automation starts as **creator** receive the creator's personal secrets, whether child sessions inherit them, and whether the blueprint test VM loads personal secrets. A safe test is a dummy personal secret (for example `TEST_SECRET_VISIBLE`) and a session that reports only whether the variable is set, never its value.

## The Devin CLI

A local terminal coding agent that runs on your machine with your repositories, shell and credentials, and can hand work off to Devin Cloud ([Devin CLI quickstart](https://docs.devin.ai/cli), [CognitionAI/devin-cli](https://github.com/CognitionAI/devin-cli)).

### Install

| Platform | Command |
| --- | --- |
| macOS (Homebrew cask) | `brew install --cask devin-cli` ([Homebrew](https://formulae.brew.sh/cask/devin-cli)) |
| macOS, Linux, WSL | `curl -fsSL https://cli.devin.ai/install.sh \| bash` |
| Windows (PowerShell) | `irm https://static.devin.ai/cli/setup.ps1 \| iex` |
| Any (npm, x64 and arm64) | `npm install -g devin` (the native binary comes from the npm registry, so it works behind a registry mirror) |

Then run `devin` in a project folder and sign in with your Devin account. Update with `npm install -g devin@latest` or your package manager.

### What it provides

* **Local work with your own credentials:** it pushes with your Git credentials and calls Databricks with your CLI profile, so you can test a task before giving Devin Cloud any access.
* **Cloud handoff and inspection:** `/handoff` continues a task in Devin Cloud; `devin --cloud` works with cloud sessions; you can SSH into a cloud session to check installed tools and which secrets are present (names only).
* **Scripting:** `devin -p` runs a single turn for scripts and CI.
* **Your existing setup:** `AGENTS.md` rules, MCP servers, `SKILL.md` skills, hooks and Claude Code plugins work as-is, so Databricks skills written for other agents can be reused.
* **Planning and safety modes:** `/plan` (agree on an approach first), `/ask` (read-only), `/loop` (implement, then review the diff), `/fork` and `/revert`.

### Using it for setup

1. Try a repository task locally first (for example adding a docs page on a feature branch) to check the prompt before automating it.
2. SSH into a cloud session to confirm the environment: Databricks CLI version, network access to the workspace, and which secret names are set.
3. Connect the CLI to a Unity Gateway MCP Service to test Databricks tools from Devin before granting them to cloud sessions.

A laptop session is not an unattended monitor. Use a Devin automation for recurring work.

## Common Pitfalls

* Using a legacy `apk_` key with the Devin MCP server: only the wiki tools work.
* Assuming tool selectors can make an action-based Devin tool read-only.
* Storing Databricks credentials as organization secrets in a shared Devin organization.
* Expecting Devin to push to a repository it can only clone (public repository, no GitHub App).
* Leaving an automation's network policy unrestricted instead of adding just the workspace host.

## References

* [Devin MCP](https://docs.devin.ai/work-with-devin/devin-mcp)
* [DeepWiki MCP](https://docs.devin.ai/work-with-devin/deepwiki-mcp)
* [Devin GitHub integration](https://docs.devin.ai/integrations/gh)
* [Devin CLI quickstart](https://docs.devin.ai/cli)
* [Authorize service principal access with OAuth](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-m2m/)
* [Register external MCP servers in Unity Gateway](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service/)
