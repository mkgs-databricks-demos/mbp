# mbp
Matt's Best Practices for Working with Databricks

| Folder | Topic |
|---|---|
| [workspace-architecture](workspace-architecture/docs/document.md) | Enterprise workspace architecture and governance reference: environments, Unity Catalog, storage, identity, networking, compute, CI/CD overview, DR |
| [developer-user-isolation-in-uc](developer-user-isolation-in-uc/docs/uc-naming-convention-reference.md) | Unity Catalog naming convention per environment, developer schema isolation, zero-hardcoding rule, grants |
| [sdlc-best-practices](sdlc-best-practices/README.md) | SDLC deep dive with Declarative Automation Bundles and GitHub Actions, including a complete example bundle and a bundle vs Terraform vs REST API comparison |
| [genie-build-waves](genie-build-waves) | Bundle for orchestrating parallel build waves |
| [unity-gateway](unity-gateway/README.md) | Registering and governing external MCP servers in Unity Gateway: auth options, permissions, invocation, pitfalls. Includes a Robinhood MCP example (proxy app for providers that only accept a loopback OAuth redirect) |

Suggested reading order: workspace architecture, then UC naming, then SDLC best practices.
