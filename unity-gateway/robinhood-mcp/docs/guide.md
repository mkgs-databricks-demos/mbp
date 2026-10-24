# Example: Governing a Brokerage MCP Server (Robinhood) Through Unity Gateway

This example applies the general pattern in the [Unity Gateway README](../../README.md) to a remote MCP server whose OAuth setup **cannot** be registered directly as a UC HTTP connection. It uses Robinhood's MCP server as the worked case, but the pattern applies to any provider that only accepts a fixed loopback redirect URL.

> Brokerage tools can move real money. Treat everything here as a starting point for a read-only integration, and review it with your security and compliance teams before exposing any write tool.

## What the Server Offers

Robinhood's remote MCP server exposes a large tool catalog (roughly 90 tools when tested in October 2026) over Streamable HTTP with server-sent events. The tools fall into two groups:

| Group | Examples | Risk |
| --- | --- | --- |
| Read | `get_*` tools (accounts, positions, quotes, orders, history), `search` | Exposes account data |
| Write | `place_equity_order`, `cancel_equity_order`, option, crypto, and advanced order tools, `exercise_option`, watchlist and alert mutations | Executes trades or changes account state |

Always read the live `tools/list` response rather than assuming tool names. Names in third-party docs, samples, or test fixtures can differ from what the server actually exposes.

## Why Direct Registration Fails

The standard pattern (UC HTTP connection with OAuth User to Machine Per User, then an MCP Service) needs the provider to redirect back to `https://<workspace-hostname>/login/oauth/http.html`. When tested in October 2026, Robinhood's OAuth server behaved as follows:

- **Dynamic client registration is a stub.** It returns the same static client ID for every registration and does not save the redirect URIs you send.
- **The redirect allowlist is fixed server-side** to a loopback URL (`http://localhost:<port>/callback`). Hosted HTTPS callbacks, including the Databricks workspace URL, are rejected on the consent screen.
- **Tokens:** PKCE authorization code flow. Access tokens last several days; refresh tokens rotate on every use, and replaying an old refresh token returns `invalid_grant`. There is no revocation endpoint.
- **The token response contains extra sensitive fields** beyond the access and refresh tokens. Treat the entire response as a secret.

Because the workspace callback can never be allowlisted, a UC HTTP connection pointed straight at the server can't complete sign-in.

## Recommended Pattern: Proxy App With a Paste-Back Connect Flow

Put a small Databricks App in front of the provider. The app owns the OAuth grant and exposes its own MCP endpoint, and Unity Gateway governs the app.

```
Genie / Agent  ->  Unity Gateway MCP Service  ->  Databricks App (MCP proxy)  ->  Robinhood MCP server
                                                         |
                                                         +-- encrypted token store
```

### Connect Flow (one-time per account)

1. An operator opens the app's **Connect** page. The app generates a PKCE verifier, `state`, and the authorization URL with the loopback redirect URI.
2. The operator signs in to the brokerage in their browser. The browser is redirected to `http://localhost:<port>/callback?code=...&state=...`, which doesn't load. That is expected.
3. The operator copies the full URL from the address bar and pastes it back into the app.
4. The app validates `state`, exchanges the code (with the PKCE verifier) from its server side, and stores the tokens.

### Token Handling

- **Encrypt at rest** with an app-held key (for example AES-GCM with the key in a Databricks secret scope). Store tokens in a database the app owns, such as Lakebase, not in workspace files or logs.
- **Single-writer refresh.** Because refresh tokens rotate, two concurrent refreshes will invalidate each other. Serialize refreshes with a lock and persist the new refresh token before using the new access token.
- **Fail closed.** On `invalid_grant`, mark the connection as needing reconnect and have downstream agents stop acting (for a trading agent, go to a safe state) until an operator reconnects.
- **Redact.** Never log token responses, and scrub provider URLs that carry keys or tokens from traces and spans.

### Tool Exposure (defense in depth)

1. **App-side allowlist.** The proxy forwards only read tools (`get_*` and `search`) and refuses everything else, even if a caller asks for it by name.
2. **MCP Service tool selectors.** Register the service with the same read-only selectors so write tools never appear in `tools/list`.
3. **Separate services for simulated trading.** If you build a simulated (paper) trading MCP for testing agents, give every tool a distinct name (for example containing `paper`) while mirroring the real tool shapes. This keeps simulated and live tools from being confused by people, agents, or policies.
4. **Expand deliberately.** Add live write tools only after the read-only and simulated paths are proven, with service policies requiring approval for order tools.

### Registering the App in Unity Gateway

1. Deploy the proxy as a Databricks App. Its MCP endpoint is protected by the Apps authentication layer.
2. Create a UC HTTP connection to the app URL that authenticates as a Databricks identity allowed to call the app, and mark it as an MCP connection.
3. Register the MCP Service on that connection with the read-only tool selectors.
4. Grant callers `USE CATALOG`, `USE SCHEMA`, and `EXECUTE` on the service. See [Permissions](../../README.md#permissions).
5. Grant the app's service principal `READ` on the secret scope holding its encryption key, and access to its token database.

## Testing Without Production Risk

- Capture `tools/list` and representative read responses as fixtures, then build agents against the fixtures or a simulated server first.
- Run sign-in tests from a notebook a human operates. Automated agents should not hold brokerage credentials or complete the consent flow.
- Re-test the provider's OAuth behavior periodically. If the provider later supports hosted redirects or approved client registration, direct registration may become possible and the proxy may no longer be needed.

## References

- [Unity Gateway README](../../README.md) for the general registration pattern, permissions, and governance
- [Register external MCP servers in Unity Gateway](https://docs.databricks.com/aws/en/ai-gateway/register-mcp-service/)
- [OAuth 2.0 for Native Apps (RFC 8252), loopback redirects](https://datatracker.ietf.org/doc/html/rfc8252)
- [Proof Key for Code Exchange (RFC 7636)](https://datatracker.ietf.org/doc/html/rfc7636)
