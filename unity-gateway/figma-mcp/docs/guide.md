# Example: Registering Figma's MCP Server in Unity Gateway

This example applies the general pattern in the [Unity Gateway README](../../README.md) to the Figma MCP server, so that Genie and other agents can retrieve design context, code, and resources from Figma files, including Figma Make projects.

## What Figma Offers

Figma provides an official MCP server in two forms:

| Server | URL | Requirements |
| --- | --- | --- |
| **Remote** (recommended) | `https://mcp.figma.com/mcp` | Figma account; Full seat for writes outside drafts |
| **Desktop** (local) | `http://127.0.0.1:3845/mcp` | Figma desktop app; Dev or Full seat on Professional/Organization/Enterprise plan |

The **remote server** is the better choice for most use cases. It has the broadest feature set and does not require the desktop app.

### Exposed Tools

| Tool | Description | Remote Only |
| --- | --- | --- |
| `get_design_context` | Design context and code for a layer or selection (supports Make files) | No |
| `get_metadata` | Lightweight XML outline of a selection | No |
| `get_screenshot` | Screenshot of a selection | No |
| `get_variable_defs` | Variables and styles used in a selection | No |
| `download_assets` | Download design assets | Yes |
| `import_codebase` | Import a local project into Figma as a Make file or code layer | Yes |

The MCP server also exposes the prompt `create_design_system_rules`.

### Figma Make Support

The MCP server indexes the code in a Make file, so an AI agent receives the actual source code rather than a rendered prototype or screenshot. `get_design_context` works on Make files, and `import_codebase` can write a project into Make.

## Option 1: Register Figma's Remote Server Directly

### Steps

1. In your Databricks workspace, go to **Unity Gateway > MCPs > + MCP > Connect an existing MCP server**.
2. Enter the MCP server URL: `https://mcp.figma.com/mcp`.
3. Create or select an HTTP connection with **OAuth User to Machine Per User** authentication.
   - Figma is **not** a Databricks managed OAuth provider. You must supply your own Figma OAuth app credentials (client ID, client secret, authorization endpoint, token endpoint).
   - Add `https://<workspace-hostname>/login/oauth/http.html` to your Figma OAuth app's allowed redirect URLs.
4. Click **Create & load tools** to discover the available tools.
5. Select the tools to expose and click **Create MCP Service**. Consider excluding `import_codebase` unless agents need to write to Figma.
6. Grant access as described in [Permissions](../../README.md#permissions).

### Known Limitation: Client Allowlist

Figma restricts remote server access to clients listed in its [MCP Catalog](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/). As of October 2026, clients such as VS Code, Cursor, Claude Desktop, and Gemini CLI are supported, but Databricks Unity Gateway is **not** on the list.

This means the OAuth sign-in step may fail because Figma does not recognize Unity Gateway as an approved client. If that happens, you have two paths:

- **Apply to Figma's waitlist** to get your Databricks integration approved as a new MCP client.
- **Build your own server** (Option 2 below).

### Desktop Server Limitation

The desktop server runs on `127.0.0.1`, which is unreachable from Databricks serverless compute. It is not a viable option for Unity Gateway registration.

## Option 2: Build a Custom Figma MCP Server as a Databricks App

If direct registration is blocked by the client allowlist, you can build a lightweight MCP server that calls the [Figma REST API](https://www.figma.com/developers/api) and deploy it as a Databricks App.

### Architecture

```
Genie / Agent  ->  Unity Gateway MCP Service  ->  Databricks App (custom MCP server)  ->  Figma REST API
```

### Implementation Outline

1. **Create a Figma OAuth app** in your Figma developer settings. Note the client ID and client secret.
2. **Build an MCP server** (Python or Node.js) that:
   - Implements `tools/list` and `tools/call` JSON-RPC methods.
   - Wraps Figma REST API endpoints (files, images, components, styles) as MCP tools.
   - Authenticates to Figma with the OAuth app credentials.
3. **Deploy as a Databricks App.** The app authenticates callers via the Apps runtime service principal.
4. **Register the app as an MCP Service** in Unity Gateway:
   - Create an HTTP connection pointing to the app's URL.
   - Register the MCP Service in the target catalog and schema.
   - Select which tools to expose.
5. **Grant access** to the MCP Service (not to the connection or the app directly).

### Considerations

- The Figma REST API provides access to files, frames, images, components, styles, and comments. Confirm that it exposes Make project source code if that is a requirement. Make-specific content retrieval via the REST API has not been verified.
- Store the Figma OAuth credentials in a Databricks secret scope and reference them from the app configuration.
- The app's service principal needs `EXECUTE` on any model services it calls downstream.

## Option 3: Use Figma's MCP Server Outside Databricks

If neither option above is viable, use Figma's MCP server directly in a supported client (VS Code, Cursor, Claude Desktop) alongside your Databricks workflows. This keeps design context available during development but does not integrate it into Genie or automated agents.

## References

- [Get started with the Figma MCP server](https://help.figma.com/hc/en-us/articles/39216419318551-Get-started-with-the-Figma-MCP-server)
- [Figma MCP tools and example prompts](https://help.figma.com/hc/en-us/articles/42495147242903-Tools-and-example-prompts)
- [Make resources and MCP](https://help.figma.com/hc/en-us/articles/42495172049303-Make-resources-and-MCP)
- [Figma MCP supported clients](https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/)
- [Unity Gateway README](../../README.md) for the general registration pattern, permissions, and governance
