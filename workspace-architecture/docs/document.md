# Enterprise Databricks Workspace Architecture & Governance Reference

## Author: Matthew Giglia | Field Engineering

---

### Executive Summary

This reference architecture defines a comprehensive workspace strategy for enterprise Databricks deployments. It covers the Unity Catalog governance foundation, storage architecture, compliance security profiles, identity and access management, networking, compute policies, environment isolation (Dev → Test → UAT → Prod), specialized workspaces (Sandbox, Interactive Analyst, Consumer/Genie Ontology), external customer access via Unity Gateway, CI/CD deployment pipelines, disaster recovery, and global operations.

The design philosophy: **if it's worth building for one customer, it's worth building for all.** Every pattern here is reusable across industries and cloud providers.

---

### Section 1: Workspace Environment Strategy

#### 1.1 The Six-Workspace Enterprise Model

The industry standard of Dev → Staging → Prod is a starting point, but enterprise customers with regulated data, consumer-facing applications, analyst populations, and innovation requirements need a more nuanced model. The recommended architecture uses **six logical workspace tiers**:

| Workspace | Purpose | Data Profile | Who Uses It | Compliance Profile |
|---|---|---|---|---|
| **Sandbox** | Pre-release feature testing, innovation spikes | Synthetic only | Platform team, innovation leads | None (minimal controls) |
| **Dev** | Developer iteration, unit testing, DAB dev-mode | Write: synthetic/dev; Read: optionally prod+tst (see §2.4) | Data engineers, ML engineers, data scientists | None, or matches prod if reading regulated data |
| **Test / UAT** | Integration testing, business validation, regression | Write: test data; Read: optionally prod (see §2.4) | QA, business analysts, UAT users | Matches prod if processing regulated data |
| **Production** | Business-critical workloads, certified pipelines | Production data | CI/CD, operators, scheduled jobs | As required per data type |
| **Interactive Analyst** | Ad-hoc SQL against production data, asset authoring | Read: prod data; Write: analyst catalog | Business analysts, data analysts | Matches prod (reads regulated data) |
| **Consumer** | Genie Ontology surface, dashboards, Genie Agents, Apps | Read-only prod (certified gold) | Business users, external consumers | Inherits from prod catalog binding |

#### 1.2 Workspace Topology Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Databricks Account                                  │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │ SANDBOX  │ │   DEV    │ │ TST/UAT  │ │   PROD   │                  │
│  │ Preview  │ │ Personal │ │ Integra- │ │ Certified│                  │
│  │ features │ │ schemas  │ │ tion &   │ │ pipelines│                  │
│  │ No prod  │ │ DAB dev  │ │ business │ │ Gold     │                  │
│  │ data     │ │ mode     │ │ valid.   │ │ tables   │                  │
│  └──────────┘ └──────────┘ └──────────┘ └──┬───┬──┘                  │
│                              ┌──────────────┘   └──────────┐          │
│                     ┌────────▼────────┐        ┌────────────▼──┐      │
│                     │  INTERACTIVE    │        │   CONSUMER    │      │
│                     │  ANALYST        │        │ Genie Agents  │      │
│                     │ Ad-hoc SQL      │        │ Genie One     │      │
│                     │ Author assets   │        │ Dashboards    │      │
│                     │ NO publishing   │        │ Apps          │      │
│                     └─────────────────┘        └───────────────┘      │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Unity Catalog Metastore (Regional)                  │   │
│  │  sandbox_cat │ func_dev │ func_tst │ func (prod) │ analyst_cat  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 1.3 Promotion Path

The code promotion path follows the Declarative Automation Bundle (DAB) model. The catalog is the environment discriminator — schema names are stable across all environments except Dev, where DAB's `dev_<user>_` prefix provides per-developer isolation.

```
Feature Branch → Dev (personalized schemas, iterate fast)
                   ↓  target_catalog changes, schema prefix drops
                 Tst (exact schema names, integration test)
                   ↓  target_catalog changes only
                 UAT (exact schema names, business validation)
                   ↓  target_catalog changes only
                 Prd (exact schema names, canonical)
                   ↓  read-only binding
                 Consumer (Genie Ontology surface)
```

**Naming convention:** `<business_function>_<env>` for non-prod (e.g., `hedis_dev`, `hedis_tst`, `hedis_uat`), plain `<business_function>` for prod (e.g., `hedis`). Only dev gets personalized schemas. In tst/uat/prd, schema names are exact matches — only the catalog name changes.

**Zero hardcoding rule:** Nothing in the bundle is hardcoded. Catalogs, schemas, table references — everything is parameterized via `${var.catalog}`, `${var.schema_prefix}`, and `${resources.<type>.<resource_id>.<element>}`.

---

### Section 2: Unity Catalog & Metastore Architecture

#### 2.1 One Metastore Per Region

Unity Catalog enforces one metastore per region. All workspaces in a region share that metastore. This is a hard constraint, not a recommendation.

#### 2.2 Cross-Region Data Access

For cross-region data sharing, use **Databricks-to-Databricks (D2D) OpenSharing**. Key considerations:

- Lineage graphs do not cross metastore boundaries
- Access control does not cross metastore boundaries — grants must be replicated at the destination
- Egress charges apply for cross-region data movement
- For frequently accessed cross-region data, consider a replication pipeline to synchronize tables rather than relying solely on OpenSharing
- Do **not** register the same external table in multiple metastores — this causes schema drift and Delta commit service consistency issues

#### 2.3 Catalog Hierarchy

Within each metastore, catalogs are organized by business function and environment:

```
Metastore (US-East)
├── hedis_dev          → bound to Dev workspace
├── hedis_tst          → bound to Test/UAT workspace
├── hedis              → ISOLATED to Prod + Consumer + Interactive Analyst + Dev (read) + Tst (read)
├── underwriting_dev   → bound to Dev workspace
├── underwriting_tst   → bound to Test/UAT workspace
├── underwriting       → ISOLATED to Prod + Consumer + Interactive Analyst + Dev (read) + Tst (read)
├── analyst            → bound to Interactive Analyst workspace only
├── sandbox            → bound to Sandbox workspace
└── system             → system tables (account-wide)
```

#### 2.4 Cross-Environment Read Access — "Read Up, Write Local"

The recommended pattern: each workspace may only **write** to its own environment catalog, but can have **read-only** access to catalogs above it in the promotion hierarchy.

```
                    WRITE ACCESS          READ ACCESS (upward only)
                    ──────────            ─────────────────────────
Sandbox WS    →    sandbox catalog        (none — synthetic only)
Dev WS        →    func_dev catalog       + READ func_tst, func (prod)
Tst/UAT WS    →    func_tst catalog       + READ func (prod)
Prod WS       →    func (prod) catalog    (top of hierarchy)
Analyst WS    →    analyst catalog         + READ func (prod)
Consumer WS   →    (no write)             + READ func (prod)
```

Schema-level grants control which medallion layers are visible — bronze, silver, or gold — based on development need. A team building gold reads prod silver; a team building silver reads prod bronze; analysts read gold.

#### 2.5 Pros and Cons of Cross-Environment Read Access

**Pros:**

| Benefit | Detail |
|---|---|
| **Eliminates wholesale data copying** | No need to copy terabytes into lower environments. Saves storage cost and eliminates sync lag. |
| **Realistic development and testing** | Validate transformations against actual production data shapes, volumes, and edge cases. |
| **Faster iteration for capable engineers** | DevOps-capable engineers develop in Dev while reading prod, then promote through CI/CD. |
| **Reference data stays current** | Lookup and dimension tables in prod are always current — no stale copies. |
| **Test validation against prod baselines** | Compare pipeline outputs against production to validate correctness. |
| **Reduced operational burden** | No data copy/sync pipelines to build and maintain. |

**Cons:**

| Risk | Mitigation |
|---|---|
| **Compliance exposure** | Any workspace reading regulated prod data must carry the same compliance security profile (§4). |
| **Accidental production dependency** | Code should be parameterized to work against any catalog; integration tests should use test data. |
| **Data leakage risk** | FGAC (column masking, row filters) on sensitive columns; egress controls; audit logging. |
| **Blast radius of misconfigured grants** | Grants at schema or table level, not catalog-wide. UC groups aligned to project teams. |
| **Not appropriate for all personas** | Grant-level decision — workspace binding makes prod visible; UC grants control who gets SELECT. |

#### 2.6 When NOT to Use Cross-Environment Read Access

- **Sandbox workspace** — should never read production data; synthetic only
- **Strict regulatory separation** — some regulations require physical data isolation between environments
- **Untrusted developer populations** — contractors, offshore teams, or users without production data authorization

---

### Section 3: Storage Architecture

#### 3.1 Managed vs. External Storage

Unity Catalog supports two storage models:

| Storage Type | Description | When to Use |
|---|---|---|
| **Managed storage** | Databricks manages the storage location; tables are created in the metastore's or catalog's default location | Default for most use cases; simplest to manage |
| **External storage** | Customer provides and manages the storage location; tables reference customer-owned buckets/containers | When you need control over storage location, encryption keys, lifecycle policies, or cross-platform access |

#### 3.2 Storage Isolation by Environment

Use **separate storage locations** for each environment to prevent accidental cross-environment data access at the cloud storage layer:

```
s3://company-data-dev/          (or abfss://dev@companydatalake.dfs.core.windows.net/)
s3://company-data-test/         (or abfss://test@companydatalake.dfs.core.windows.net/)
s3://company-data-prod/         (or abfss://prod@companydatalake.dfs.core.windows.net/)
s3://company-data-analyst/      (or abfss://analyst@companydatalake.dfs.core.windows.net/)
```

For stronger isolation, use separate:
- Cloud storage accounts or buckets per environment
- IAM roles or managed identities per environment
- Encryption keys (BYOK/CMK) per environment where required
- Storage credentials in UC per environment

#### 3.3 External Locations & Storage Credentials

- **Storage credentials** — represent the cloud IAM identity (role, managed identity, service account) that accesses storage. Bind to specific workspaces to prevent cross-environment credential use.
- **External locations** — map a cloud storage path to a storage credential. Bind to specific workspaces using workspace binding (same mechanism as catalog binding).
- **Principle:** storage credentials and external locations should be bound to the same workspaces as the catalogs they serve. A prod storage credential should not be accessible from the Dev workspace.

#### 3.4 Encryption Considerations

| Requirement | Approach |
|---|---|
| Default encryption | Cloud provider default (SSE-S3, Azure Storage encryption, Google-managed) |
| Customer-managed keys (CMK/BYOK) | Configure per storage account; required for some compliance standards |
| Separate keys per environment | Use different CMK keys for prod vs. non-prod to limit blast radius of key compromise |
| Key rotation | Automate via cloud KMS; ensure Databricks storage credentials reference the current key |

---

### Section 4: Compliance Security Profile — Targeted, Not Blanket

#### 4.1 The Problem with Blanket Application

The Enhanced Security and Compliance add-on provides critical controls for regulated data: hardened compute images, enhanced security monitoring, automatic cluster updates, and compliance standard alignment (HIPAA, HITRUST, PCI-DSS, etc.).

However, **blanket-applying the compliance security profile to all workspaces is an anti-pattern** because:

- It adds cost (the Enhanced Security and Compliance add-on is a paid feature)
- It restricts preview features — Partner-powered AI features (including Genie Code) are disabled by default on compliance-profiled workspaces
- It limits compute instance types to those supporting VNet encryption
- It is **permanent** — once a workspace has processed regulated data under a compliance standard, the profile cannot be disabled; the workspace must be deleted and recreated
- Not all workspaces process regulated data — dev and sandbox workspaces using synthetic data don't need HIPAA controls

#### 4.2 Targeted Compliance Profile Assignment

| Workspace | Compliance Profile | Rationale |
|---|---|---|
| **Sandbox** | None | Synthetic data only, preview feature testing |
| **Dev** | None if synthetic only; match prod if reading regulated prod data (see §2.4) | Compliance profile follows the data |
| **Test / UAT** | Match prod if testing with representative regulated data | Must mirror prod controls if regulated data flows through |
| **Production** | HIPAA, PCI-DSS, HITRUST, etc. as required | Processes actual regulated data |
| **Interactive Analyst** | Match prod (reads regulated production data) | Analysts query prod tables containing PxI data |
| **Consumer** | Match prod if serving regulated data to end users | Inherits requirement from the data it surfaces |

**The rule:** the compliance profile follows the **data**, not the workspace.

#### 4.3 Multi-Standard Workspaces

For organizations processing different data types with different compliance requirements, consider **separate production workspaces per compliance domain**:

```
Production (HIPAA) — clinical/PHI data pipelines
Production (PCI-DSS) — payment card data pipelines
Production (standard) — non-regulated analytics
Consumer (HIPAA) — clinical Genie Agents and dashboards
Consumer (standard) — non-regulated BI
```

---

### Section 5: Identity & Access Management

#### 5.1 Account-Level Identity Foundation

All identity management should be centralized at the **Databricks account level**, not per-workspace:

- **SSO** — configure account-level SSO with the enterprise IdP (Okta, Azure AD/Entra ID, etc.)
- **SCIM** — enable automatic identity provisioning to sync users and groups from the IdP to Databricks
- **Account-level groups** — define groups once, use them across all workspaces and UC grants

#### 5.2 Group Strategy

| Group | Purpose | Workspace Access | UC Grants |
|---|---|---|---|
| `platform-admins` | Account and workspace administration | All workspaces | Metastore admin (optional) |
| `dev-engineers` | Data engineers, ML engineers | Dev, Tst/UAT | R/W on dev/tst catalogs; READ on prod catalogs |
| `qa-testers` | QA and integration testing | Tst/UAT | R/W on tst catalogs; READ on prod catalogs |
| `analysts` | Business analysts, data analysts | Interactive Analyst | R/W on analyst catalog; READ on prod gold |
| `prod-operators` | Production job monitoring, incident response | Production | Limited operational access |
| `consumers` | Business users, dashboard viewers | Consumer | READ on prod gold, metric views, Pages |
| `ci-cd-deployers` | Service principals for automated deployment | Per-target workspace | Per-environment deployment grants |

#### 5.3 Service Principal Strategy

| SPN | Purpose | Scope |
|---|---|---|
| **Dev deployment SPN** | DAB deployment to Dev workspace | Dev workspace + dev catalogs |
| **Tst deployment SPN** | DAB deployment to Tst/UAT workspace | Tst workspace + tst catalogs |
| **Prod deployment SPN** | DAB deployment to Prod workspace | Prod workspace + prod catalogs |
| **App SPN** | Databricks App runtime operations | Consumer workspace + Lakebase + UC read |
| **Pipeline SPN** | Lakeflow pipeline execution | Prod workspace + prod catalogs (R/W) |

**Key principles:**
- Separate deployment SPNs per environment for separation of duties
- Use **Workload Identity Federation** for CI/CD — no long-lived secrets in GitHub/Azure DevOps
- App SPNs get auto-injected credentials via the Databricks Apps runtime
- Never use personal access tokens (PATs) in CI/CD pipelines

#### 5.4 Workspace Entitlements

Control what users can do within each workspace:

| Entitlement | Sandbox | Dev | Tst/UAT | Prod | Analyst | Consumer |
|---|---|---|---|---|---|---|
| Workspace access | ✓ | ✓ | ✓ | Limited | ✓ | ✓ |
| Create clusters | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| SQL warehouse access | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create notebooks | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| Create jobs | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| Databricks SQL access | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Genie access | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

### Section 6: Networking & Data Plane Isolation

#### 6.1 Network Architecture by Workspace Tier

| Workspace | Network Posture | Rationale |
|---|---|---|
| **Sandbox** | Standard (Databricks-managed VPC/VNet) | Minimal controls, synthetic data only |
| **Dev** | Standard or BYOVPC depending on prod read access | If reading regulated prod data, network controls should match |
| **Test / UAT** | BYOVPC with controlled egress | Mirror prod network posture for realistic testing |
| **Production** | BYOVPC, private connectivity, restricted egress | Maximum protection for production data |
| **Interactive Analyst** | BYOVPC with controlled egress | Reads regulated prod data; egress controls prevent exfiltration |
| **Consumer** | BYOVPC, private connectivity if serving external customers | Network boundary for external-facing services |

#### 6.2 Private Connectivity

For production and regulated workspaces:

- **Private Link / Private Endpoints** — connect to the Databricks control plane without traversing the public internet
- **Private connectivity to cloud storage** — ensure data never leaves the private network
- **Private connectivity to Lakebase** — if using Lakebase for app state
- **Serverless network policies** — configure network access for serverless SQL warehouses and compute

#### 6.3 Egress Controls & Data Exfiltration Prevention

- Restrict outbound internet access from production and analyst workspaces
- Use network policies to control which external endpoints serverless compute can reach
- IP access lists to restrict which networks can access the workspace
- Combine with UC FGAC (column masking, row filters) for defense in depth

#### 6.4 When to Use Separate Cloud Accounts/Subscriptions

Use separate cloud accounts or subscriptions when:
- Regulatory requirements mandate physical isolation (not just logical)
- You need separate billing boundaries per environment
- IAM blast radius must be contained (a compromised prod IAM role can't reach dev resources)
- Network peering or firewall rules differ materially between environments

For most organizations, **network-level isolation within a single account** (separate VPCs/VNets per workspace) combined with UC catalog binding provides sufficient isolation. Separate accounts add operational complexity.

---

### Section 7: Compute Policy Standards

#### 7.1 Compute Policies by Workspace Tier

| Policy Attribute | Sandbox | Dev | Tst/UAT | Prod | Analyst | Consumer |
|---|---|---|---|---|---|---|
| **All-purpose clusters** | Permitted | Permitted with limits | Restricted | Restricted | Restricted | Not permitted |
| **Job clusters** | Permitted | Preferred | Required | Required | Permitted | N/A |
| **SQL warehouses** | Small | Medium | Prod-like | Right-sized | Interactive-sized | Genie/BI-sized |
| **Auto-termination** | 30 min | 60 min | 30 min | Workload-specific | 30 min | Managed |
| **Max workers** | Low | Medium | Prod-like | Approved limit | Medium | Managed |
| **Serverless** | Optional | Preferred | Preferred | Preferred | Preferred | Preferred |
| **Photon** | Optional | Optional | Match prod | Enabled | Enabled | Enabled |
| **UC-compatible access mode** | Required | Required | Required | Required | Required | Required |

#### 7.2 SQL Warehouse Strategy

Each workspace tier should have its own SQL warehouses to prevent compute contention:

| Workspace | Warehouse Purpose | Sizing Guidance |
|---|---|---|
| **Dev** | Developer ad-hoc queries, notebook execution | Small-Medium, auto-stop aggressive |
| **Tst/UAT** | Integration test execution, UAT queries | Mirror prod sizing for realistic testing |
| **Production** | Pipeline execution, scheduled jobs | Right-sized per workload SLA |
| **Interactive Analyst** | Ad-hoc analyst SQL, dashboard development | Medium, optimized for interactive latency |
| **Consumer** | Genie Agent queries, dashboard rendering, App queries | Sized for concurrent user load |

#### 7.3 Tagging Requirements for FinOps

All compute resources should carry mandatory tags:

```
environment: dev | tst | uat | prod | sandbox | analyst | consumer
project: <business_function>
team: <owning_team>
cost_center: <finance_code>
workload_type: interactive | pipeline | genie | app
```

Tags enable cost allocation, chargeback, and anomaly detection across workspaces.

---

### Section 8: The Sandbox Workspace

#### 8.1 Why a Sandbox?

Databricks releases features through Private Preview → Public Preview → GA. The sandbox workspace provides a **completely isolated environment** for:

- **Pre-release feature validation** — test preview features without risk to active development
- **Innovation spikes** — prototype with new capabilities without affecting team workflows
- **Platform team evaluation** — assess feature readiness before enabling account-wide
- **Training and enablement** — hands-on workshops run in sandbox, not in environments with real data

#### 8.2 Sandbox Guardrails

| Control | Sandbox Setting |
|---|---|
| Data | Synthetic only — **never** production or masked production data |
| Catalog binding | Sandbox catalog bound only to sandbox workspace |
| Compliance profile | None |
| Compute | Minimal cluster policies, auto-termination enforced |
| Lifecycle | Ephemeral — `bundle destroy` cleans up after evaluation periods |
| Network | Standard (no private connectivity required) |
| Identity | Same IdP groups, sandbox-specific entitlements |

#### 8.3 Sandbox → Dev Promotion Gate

When the platform team validates a preview feature in sandbox:

1. Document the feature behavior, limitations, and configuration requirements
2. Enable the feature in the Dev workspace
3. Update DAB templates and cluster policies to support the feature
4. Communicate availability to engineering teams
5. The feature follows the normal Dev → Tst → UAT → Prd promotion path

---

### Section 9: The Interactive Analyst Workspace & Frictionless Analyst Deployments

#### 9.1 Why a Dedicated Interactive Analyst Workspace?

Analysts create Gold-level assets critical for data-driven decision making. They need to write SQL against production data, build notebooks, create tables, author dashboards, and develop workflows. But they **should not deploy directly to production** — that would violate SDLC governance.

The tension: enforcing full DevOps and Engineering best practices would cause **too much friction** for widespread analyst adoption. There are too many analysts, dashboards, projects, and reports for any centralized DevOps team to support.

The Interactive Analyst Workspace provides:

- **Full read access to production data** — analysts query production tables directly via SQL warehouses
- **A dedicated analyst catalog** — USE CATALOG, CREATE SCHEMA, author assets without risk of altering production
- **No direct publishing to production** — artifacts must go through the Frictionless Analyst Deployment process
- **Compute isolation** — analyst queries don't compete with production pipelines or consumer Genie workloads

#### 9.2 Frictionless Analyst Deployments — The Bridge to Production

A **Databricks App** abstracts the entire CI/CD process so analysts never need to learn Git, DABs, or DevOps tooling:

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRICTIONLESS ANALYST DEPLOYMENT PROCESS                            │
│                                                                     │
│  1. Analyst authors & tests assets in Interactive Analyst Workspace │
│  2. Analyst opens "Request Publication" Databricks App              │
│  3. App collects governance metadata:                               │
│     • Tags (FinOps) • Data Class (PxI) • Business Purpose          │
│     • Stakeholders • Failure Notification Rules                     │
│     • Schedule/Trigger Rules • Dependencies                         │
│  4. Python SDK retrieves Asset IDs                                  │
│  5. `databricks bundle generate` creates a DAB from the assets      │
│  6. Bundle written to feature branch in Data Management Repo        │
│  7. Change Control review (human approval gate)                     │
│  8. If approved → GitHub Actions: CI to Dev → CD to Stage → Prod   │
│  9. Once in Prod → Consumer Access (Databricks One, RBAC/ABAC)     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 9.3 Catalog Access Model

```
Interactive Analyst Workspace
  ├── Read:  prod catalog (granted schemas, FGAC enforced)
  ├── Write: analyst catalog (USE CATALOG, CREATE SCHEMA)
  └── None:  dev catalog, test catalog, sandbox catalog
```

---

### Section 10: The Consumer Workspace (Genie Ontology Layer)

#### 10.1 Why a Dedicated Consumer Workspace?

The consumer workspace is the **governed presentation layer** where business users and external consumers interact with certified data assets through Genie Ontology:

- **Blast radius isolation** — Genie Agent workloads don't compete with production pipeline compute
- **Tailored compute** — SQL warehouses sized for interactive BI and Genie
- **Simplified access** — business users access the consumer workspace without exposure to pipeline infrastructure
- **Genie One customization** — homepage branded and curated for the business audience

#### 10.2 What Lives in the Consumer Workspace

| Asset Type | Description | Source |
|---|---|---|
| **Genie Agents** | Curated per business domain | Deployed via DAB |
| **Genie One** | Account-level discovery surface | Platform feature |
| **Dashboards** | Certified Lakeview dashboards | Deployed via DAB |
| **Metric Views** | Certified business metrics (MEASURE()) | Defined in prod catalog |
| **UC Pages** | Business term definitions | Defined in prod catalog |
| **Databricks Apps** | Consumer-facing applications | Deployed via two-bundle DAB |

#### 10.3 Genie Ontology Architecture

Genie Ontology is the unified context layer that gives Genie One and Genie Code a business-aware map of the organization. It combines **Unity Catalog Semantics** (metric views, domains, Pages) with **Inferred Context** (snippets extracted from dashboards, SQL queries, and Genie Agents).

**The key insight:** the same metric views serve both the consumer app AND internal enterprise Genie Agents — one semantic layer, two audiences.

---

### Section 11: External Customer Access — Unity Gateway + Hyperscaler API Gateway

#### 11.1 The Problem

External customers (health plan members, banking app users, partner organizations) need to access Databricks-powered capabilities but are **not Databricks account users**.

#### 11.2 The Architecture

A **hyperscaler API gateway** (Azure APIM, AWS API Gateway, GCP Apigee) sits between external customers and Databricks:

```
External Customer → API Gateway → Databricks Consumer Workspace
                    (auth, rate    ├── Databricks App (OBO via Lakebase)
                     limiting,     ├── Unity Gateway (MCP, Models, Skills)
                     validation)   └── Model Serving Endpoints
```

#### 11.3 The Three-SPN Architecture

| SPN | Purpose | Blast Radius |
|---|---|---|
| **App SPN** | Databricks App server operations | App-scoped |
| **Gateway SPN** | Unity Gateway model/MCP calls | AI-scoped |
| **External Bootstrap SPN** | API gateway → Databricks auth | Minimal (CAN_USE on app only) |

#### 11.4 On-Behalf-Of (OBO) Pattern

1. External customer authenticates to API gateway (API key, OAuth client credentials, mTLS)
2. API gateway validates and forwards to Databricks App endpoint
3. App looks up external identity in Lakebase user registry
4. App executes Databricks operations using its own M2M OAuth SPN
5. External caller's identity preserved in data columns for lineage and audit
6. All operations logged via MLflow 3 tracing

#### 11.5 Unity Gateway Governance

- **Access control** — UC ACLs on model services, MCP servers, and skills
- **Rate limiting** — service policies attached to model services
- **Guardrails** — sensitive data detection, content filtering
- **Audit logging** — all requests logged for compliance
- **Cost management** — token and request tracking per endpoint
- **Fallback routing** — automatic failover between model providers

---

### Section 12: CI/CD & Deployment Pipelines

#### 12.1 Declarative Automation Bundles (DABs)

DABs are the recommended IaC and deployment mechanism for packaging source code, jobs, pipelines, permissions, tests, and environment-specific configuration.

#### 12.2 DAB Target Configuration

```yaml
targets:
  dev:
    mode: development    # enables dev_ schema prefix
    workspace:
      host: ${var.dev_host}
    variables:
      catalog: hedis_dev

  tst:
    workspace:
      host: ${var.tst_host}
    variables:
      catalog: hedis_tst

  prod:
    workspace:
      host: ${var.prod_host}
    variables:
      catalog: hedis
```

#### 12.3 Two-Bundle DAB Pattern (for projects with Databricks Apps)

- **Bundle 1 (Infra):** UC schemas, tables, volumes, Lakeflow pipelines (SDP), Lakeflow Jobs, Lakebase project + environment branches. Deployed first.
- **Bundle 2 (App):** Databricks App. Initialized via `databricks apps init` from a serverless compute notebook terminal with plugin selection (Lakebase, OpenTelemetry, Data API). Deployed after Bundle 1.

Bundle 1 must be fully deployed and validated before Bundle 2 is initialized — the app depends on Bundle 1's resources.

#### 12.4 CI/CD Pipeline Structure

```
Feature Branch
   ├── Unit tests, linting, security scanning
   ├── Bundle validation (`databricks bundle validate`)
   └── PR review
          ↓
Merge to main
          ↓
GitHub Actions / Azure DevOps:
   ├── CI: Deploy to Dev (automatic)
   ├── CD: Deploy to Tst/UAT (automatic)
   │   ├── Integration tests
   │   ├── Data quality tests
   │   └── UAT approval gate
   └── CD: Deploy to Prod (manual approval)
          ├── Smoke tests
          └── Post-deployment validation
```

#### 12.5 Deployment Controls

| Control | Dev | Tst/UAT | Prod |
|---|---|---|---|
| Trigger | Automatic on merge | Automatic after Dev | Manual approval required |
| SPN | Dev deployment SPN | Tst deployment SPN | Prod deployment SPN |
| Auth | Workload Identity Federation | Workload Identity Federation | Workload Identity Federation |
| Rollback | `bundle destroy` + redeploy | `bundle destroy` + redeploy | Revert to previous validated release |
| Audit | Commit SHA, deployer, timestamp | Commit SHA, deployer, timestamp | Commit SHA, approver, deployer, timestamp |

#### 12.6 Lifecycle Cleanup

- Lower environments (dev, tst, uat) can be cleaned up with `databricks bundle destroy`
- `bundle destroy` is DAB-aware — tears down exactly what the bundle deployed
- Dev schemas can be cleaned up individually or the entire dev catalog can be dropped
- This addresses metastore clutter: dev catalogs are ephemeral with a built-in automated teardown path

---

### Section 13: Disaster Recovery & Global Operations

#### 13.1 DR Architecture

The recommended pattern is **active-passive, single-writer** with Managed DR where available (gated feature on AWS and Azure).

#### 13.2 RTO/RPO by Workload Tier

| Workload Tier | Example | Target RTO | Target RPO | Pattern |
|---|---|---|---|---|
| Mission-critical | Real-time claims, payments | < 1 hour | < 15 min | Managed DR with continuous replication |
| Important batch | Daily ETL, gold refresh | < 4 hours | < 1 hour | Active-passive with frequent replication |
| Analytics / BI | Dashboards, Genie Agents | < 24 hours | < 24 hours | Rebuild from IaC + data replication |

#### 13.3 What Must Be Replicated

- **Data:** Bronze, silver, gold Delta tables; streaming checkpoints; volumes
- **Identity:** Users, groups, service principals, grants (account-level SSO + SCIM)
- **Code:** DABs, Terraform, notebooks — all in Git, deployed to both regions
- **Infrastructure:** Networking, private connectivity, IAM, secrets, firewall rules
- **External systems:** Kafka/Event Hubs, schedulers, BI tools, APIs, DNS

#### 13.4 Global Operations Model

For multi-geography organizations:

- Each region has its own metastore (UC hard constraint)
- D2D OpenSharing for cross-region reference data and aggregates
- Data sovereignty (GDPR, data residency) enforced at metastore + catalog binding level
- Not every region needs every workspace tier — centralize Dev/Sandbox in primary region, deploy Prod + Consumer per region
- DR pairs are region-to-region within the same cloud provider

---

### Section 14: Complete Architecture — Putting It All Together

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATABRICKS ACCOUNT                              │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  UNITY CATALOG METASTORE (Regional)                            │      │
│  │  Catalogs: sandbox | func_dev | func_tst | func (prod) | analyst│     │
│  │  "Read Up, Write Local" — cross-env read via binding + grants  │      │
│  │  Storage: separate locations + credentials per environment     │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                           │
│  │Sandbox │ │  Dev   │ │Tst/UAT │ │  Prod  │                           │
│  │No CSP  │ │CSP if  │ │CSP if  │ │HIPAA   │                           │
│  │Std net │ │reading │ │regulatd│ │PCI-DSS │                           │
│  │        │ │prod    │ │BYOVPC  │ │Pvt Link│                           │
│  └────────┘ └────────┘ └────────┘ └──┬──┬──┘                           │
│                        ┌─────────────┘  └──────────┐                   │
│                ┌───────▼───────┐          ┌─────────▼─────┐            │
│                │ Interactive   │          │   Consumer    │            │
│                │ Analyst       │          │   Genie One   │            │
│                │ Frictionless  │          │   Genie Agents│            │
│                │ Deployments   │          │   Apps        │            │
│                └───────────────┘          └───────┬───────┘            │
│                                                   │                    │
│  ┌───────────────────────────────────────────┼────────────────┐   │
│  │  EXTERNAL ACCESS: API Gateway → App/Gateway/Models             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  CI/CD: Git → DAB Bundle 1 (Infra) → DAB Bundle 2 (App)     │      │
│  │  Workload Identity Federation | Per-env deployment SPNs      │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────┐      │
│  │  DR: Primary ◄── Managed DR ──► Secondary                    │      │
│  │  Stable URL | Quarterly failover testing                      │      │
│  └────────────────────────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────┘
```

---

### Section 15: Decision Framework

#### When to Add a Workspace

| Question | If Yes → | If No → |
|---|---|---|
| Does this workload process data under a different compliance standard? | Separate workspace | Same workspace, separate catalog |
| Do users need different network boundaries? | Separate workspace | Same workspace |
| Does compute contention affect business SLAs? | Separate workspace | Same workspace, separate warehouses |
| Do teams need different workspace admin settings? | Separate workspace | Same workspace |
| Is this a preview feature evaluation? | Sandbox workspace | Dev workspace |
| Do analysts need ad-hoc SQL access to production data? | Interactive Analyst workspace | Consumer workspace (Genie/dashboards) |
| Is this a consumer-facing surface? | Consumer workspace | Production workspace |

#### When to Add a Region

| Question | If Yes → |
|---|---|
| Data sovereignty requires data to stay in-region | New metastore + regional workspaces |
| Latency requirements for regional users | New metastore + regional workspaces |
| DR requires cross-region failover | Secondary region with DR workspaces |
| Regulatory isolation (e.g., GovCloud) | Separate account + region |

---

### Section 16: Key References

- **Databricks Developer Best Practices** — workspace isolation, catalog binding, CI/CD
- **Unity Catalog Best Practices** — one metastore per region, catalog isolation, D2D OpenSharing
- **Compliance Security Profile** — HIPAA, PCI-DSS, HITRUST controls and limitations
- **Workspace-Catalog Binding** — ISOLATED mode enforcement across platform
- **Managed Disaster Recovery** — replication, failover, stable URLs
- **Unity Gateway** — AI governance, model services, MCP servers, service policies
- **Genie Ontology** — unified context layer for Genie One and Genie Code
- **Declarative Automation Bundles** — IaC for workspace configuration and deployment
- **Frictionless Analyst Deployments** — [Lucid Spark Diagram](https://lucid.app/lucidspark/1ad1687e-15b7-4728-b8fa-0a17ecdbb8bc/edit?invitationId=inv_09a27c62-ae2d-434f-91e8-8c337f1e5bf5&page=0_0#) — analyst self-service deployment process via Databricks App + `bundle generate`
