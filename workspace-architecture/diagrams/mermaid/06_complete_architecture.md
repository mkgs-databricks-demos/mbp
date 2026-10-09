%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#FF3621',
    'primaryTextColor': '#FFFFFF',
    'primaryBorderColor': '#CC2B1A',
    'secondaryColor': '#1B3139',
    'secondaryTextColor': '#FFFFFF',
    'secondaryBorderColor': '#0F1D22',
    'tertiaryColor': '#F2F2F2',
    'tertiaryTextColor': '#1B3139',
    'tertiaryBorderColor': '#E8E8E8',
    'lineColor': '#6B7280',
    'textColor': '#1B3139',
    'fontSize': '14px',
    'fontFamily': 'DM Sans, Inter, Segoe UI, sans-serif'
  }
}}%%

graph TB
    subgraph ACCOUNT["DATABRICKS ACCOUNT"]
        direction TB

        subgraph UC_LAYER["Unity Catalog Metastore · Regional"]
            UC_NOTE["Catalogs: sandbox | func_dev | func_tst | func prod | analyst\nRead Up, Write Local · Separate storage per environment"]
        end

        subgraph WORKSPACES["Workspaces"]
            direction LR
            SBX["Sandbox\nNo CSP"]
            DEV["Dev\nCSP if\nreading prod"]
            TST["Tst/UAT\nCSP if\nregulated"]
            PRD["Prod\nHIPAA\nPCI-DSS"]
        end

        PRD --> ANA["Interactive Analyst\nFrictionless Deployments\nCSP matches prod"]
        PRD --> CON["Consumer\nGenie One · Genie Agents\nDashboards · Apps"]

        subgraph EXTERNAL["External Access Layer"]
            EXT_CUST["External Customers"] --> APIGW["API Gateway\nAPIM / AWS GW / Apigee"]
            APIGW --> APP["Databricks App\nOBO via Lakebase"]
            APIGW --> UGW["Unity Gateway\nMCP · Models · Skills"]
            APIGW --> MSE["Model Serving\nEndpoints"]
        end

        CON --- EXTERNAL

        subgraph CICD["CI/CD"]
            GIT["Git"] --> B1["DAB Bundle 1\nInfra"]
            B1 --> B2["DAB Bundle 2\nApp"]
            TF["Terraform"] --> WP["Workspace\nProvisioning"]
            WIF["Workload Identity Federation\nNo long-lived secrets"]
        end

        subgraph DR["Disaster Recovery"]
            DR_P["Primary"] <-->|"Managed DR"| DR_S["Secondary"]
            DR_URL["Stable URL · Quarterly failover testing"]
        end
    end

    classDef prod fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:2px
    classDef dev fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:2px
    classDef sandbox fill:#FFAB00,stroke:#CC8800,color:#1B3139,stroke-width:2px
    classDef analyst fill:#00A972,stroke:#007A52,color:#FFF,stroke-width:2px
    classDef consumer fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:2px
    classDef uc fill:#F2F2F2,stroke:#1B3139,color:#1B3139,stroke-width:2px
    classDef external fill:#F2F2F2,stroke:#FF3621,color:#1B3139,stroke-width:1px
    classDef cicd fill:#F2F2F2,stroke:#077A9D,color:#1B3139,stroke-width:1px
    classDef dr fill:#F2F2F2,stroke:#00A972,color:#1B3139,stroke-width:1px

    class SBX sandbox
    class DEV,TST dev
    class PRD prod
    class ANA analyst
    class CON consumer
    class UC_NOTE uc
    class EXT_CUST,APIGW,APP,UGW,MSE external
    class GIT,B1,B2,TF,WP,WIF cicd
    class DR_P,DR_S,DR_URL dr
