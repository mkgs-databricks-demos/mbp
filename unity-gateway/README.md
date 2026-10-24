# Unity Gateway Best Practices

Unity Gateway exposes models and MCP servers as governed services in Unity Catalog. Each service has a three-part name (`<catalog>.<schema>.<service>`). Callers receive `EXECUTE` on the service and never need direct access to its destinations or stored credentials.

This folder covers general patterns for registering external MCP servers, plus worked examples for specific providers.

## Examples

| Example | Topic |
| --- | --- |
| [robinhood-mcp](robinhood-mcp/docs/guide.md) | A brokerage MCP server whose OAuth only accepts a fixed loopback redirect: proxy Databricks App with a paste-back connect flow, encrypted token handling, read-only tool allowlist, and Unity Gateway registration |

## Choose the Right Service Type

| Need | Use |
| --- | --- |
| A Databricks-hosted model with no custom routing | An existing `system.ai.<model>` service |
| Custom name, routing, fallbacks, quotas, or policies for a model | A model service in your own catalog and schema |
| Your own external provider account (bring your own key) | A model provider service, then route a model service to it |
| A third-party or self-hosted MCP server | An MCP Service backed by a UC HTTP connection |
| Slack, GitHub, Atlassian, Google Drive/Calendar/Gmail, Microsoft 365 | A Databricks-provided MCP in `system.ai` (no registration needed) |

## Registering an External MCP Server

### Prerequisites

- The server must be reachable from the workspace's serverless compute plane and allowed by its serverless network policy. Servers bound to `localhost` or a desktop app are not reachable.
- The creator needs `USE CATALOG`, `USE SCHEMA`, and `CREATE SERVICE` on the target schema, plus `CREATE CONNECTION` (or `USE CONNECTION` on an existing connection).
- Decide how the server authenticates (see the table below).

### Authentication Options

| Situation | Connection setup |
| --- | --- |
| Provider is on the [managed OAuth list](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-oauth/) | **OAuth User to Machine Per User**, choose the provider. Databricks manages the OAuth app. |
| Provider supports standard OAuth with your own app | **OAuth User to Machine Per User**, manual configuration: client ID, client secret, authorization and token endpoints, scopes. Add `https://<workspace-hostname>/login/oauth/http.html` to the app's redirect URLs. |
| Provider uses a static token or API key | Bearer token connection. Every caller shares the same identity at the provider. |

Prefer per-user OAuth when the provider enforces per-user access, so each caller only sees what their own account can see.

### Steps

1. **Create the connection and register the service.** In the workspace, go to **Unity Gateway > MCPs > + MCP > Connect an existing MCP server**. Choose the catalog, schema, and name (the name can't be changed later), then select an existing HTTP connection or create one inline. Use a schema-level connection for new MCPs.
2. **Load and select tools.** Click **Create & load tools**, complete **Login** if prompted, and choose which tools to expose. Selectors accept exact names or prefixes ending in `*`. Unselected tools do not appear in `tools/list` and cannot be called.
3. **Create the MCP Service.**
4. **Grant access** (see Permissions below).
5. **Use it.** Add the MCP Service to Genie Code in its MCP settings, add it to an agent, or call it from an external MCP client.

MCP Services have no SQL DDL (there is no `CREATE MCP SERVICE`). For automation, use the Python SDK or REST API:

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import catalog as c

w = WorkspaceClient()

w.ai_gateway.create_mcp_service(
    parent="schemas/<catalog>.<schema>",
    mcp_service_id="<service_name>",
    mcp_service=c.McpService(
        comment="<description>",
        config=c.McpServiceConfig(
            include_tool_selectors=["<tool_prefix>_*"],
            source_connection=c.McpServiceConfigSourceConnection(
                name="connections/<catalog>.<schema>.<connection_name>"
            ),
        ),
    ),
)
```

On an SDK version without `w.ai_gateway`, upgrade `databricks-sdk`, or call `POST /api/2.1/unity-catalog/mcp-services` with `parent` and `mcp_service_id` query parameters and the same body.

### Invoking the Service

All MCP operations go through one JSON-RPC endpoint:

```
POST https://<workspace-hostname>/ai-gateway/mcp-services/<catalog>.<schema>.<service_name>
```

Use `tools/list` to discover tools and `tools/call` with `params.name` and `params.arguments` to invoke one. When connecting with on-behalf-of user authentication, include the `ai-gateway` OAuth scope.

## Permissions

| Grant | Target | Who |
| --- | --- | --- |
| `USE CATALOG` | Parent catalog | Every caller |
| `USE SCHEMA` | Parent schema | Every caller |
| `EXECUTE` | MCP Service | Every caller |
| `CREATE SERVICE` | Schema | Service creator |
| `CREATE CONNECTION` or `USE CONNECTION` | Schema or connection | Service creator only |

- **Never grant `USE CONNECTION` to end users.** It lets them bypass the MCP Service's tool selection, policies, and audit path.
- For a Databricks App, grant privileges to the app's service principal, not to the person who deployed it.
- Grant to groups rather than individual users.

## Governance and Observability

- **Tool selection** limits the attack surface. Expose only the tools a workload needs, and prefer read-only tools unless writes are required.
- **Service policies** evaluate calls before execution for guardrails or custom allow, deny, and approval behavior.
- **Usage** is recorded in `system.ai_gateway.usage`. Filter by service type or fully qualified service name.
- **Unified tracing** is a one-time metastore-level setup (**Unity Gateway > Govern > Traces > Set up tracing**), not a per-service setting.

## Common Pitfalls

- Registering a server that only listens on `localhost` (desktop apps, local dev servers).
- Forgetting the workspace redirect URL on a custom OAuth app.
- Assuming every hosted MCP server accepts any client. Some providers only allow approved MCP clients, or only accept a fixed loopback redirect URL, so the workspace callback can never be allowlisted. Check the provider's OAuth metadata and documentation before planning an integration, and use a proxy Databricks App when direct registration isn't possible (see the robinhood-mcp example).
- Granting `USE CONNECTION` to callers instead of `EXECUTE` on the service.

## References

- [Register external MCP servers in Unity Gateway](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service/)
- [Managed OAuth providers](https://docs.databricks.com/aws/en/agents/mcp-tools/managed-oauth/)
- [Databricks-provided MCPs](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services/)
- [Connect to external HTTP services](https://docs.databricks.com/aws/en/query-federation/http/)
- [Connect Genie Code to MCP servers](https://docs.databricks.com/aws/en/genie-code/mcp/)
