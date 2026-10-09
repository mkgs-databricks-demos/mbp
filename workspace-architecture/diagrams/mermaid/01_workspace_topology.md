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
    subgraph ACCOUNT["Databricks Account"]
        direction TB

        subgraph SDLC["SDLC Workspaces"]
            direction LR
            SANDBOX["SANDBOX\nPreview features\nSynthetic data only\nNo CSP"]
            DEV["DEV\nPersonal schemas\nDAB dev mode"]
            TST["TST / UAT\nIntegration &\nbusiness validation"]
            PROD["PRODUCTION\nCertified pipelines\nGold tables\nHIPAA / PCI-DSS"]
        end

        PROD -->|read-only| ANALYST["INTERACTIVE\nANALYST\nAd-hoc SQL\nAuthor assets\nNO publishing"]
        PROD -->|read-only| CONSUMER["CONSUMER\nGenie Agents\nGenie One\nDashboards\nApps"]

        subgraph UC["Unity Catalog Metastore · Regional"]
            direction LR
            C_SBX["sandbox_cat"]
            C_DEV["func_dev"]
            C_TST["func_tst"]
            C_PROD["func · prod"]
            C_ANA["analyst_cat"]
        end
    end

    SANDBOX -.->|bound| C_SBX
    DEV -.->|bound| C_DEV
    TST -.->|bound| C_TST
    PROD -.->|ISOLATED| C_PROD
    ANALYST -.->|bound| C_ANA
    CONSUMER -.->|read-only| C_PROD

    classDef prod fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:2px
    classDef dev fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:2px
    classDef sandbox fill:#FFAB00,stroke:#CC8800,color:#1B3139,stroke-width:2px
    classDef analyst fill:#00A972,stroke:#007A52,color:#FFF,stroke-width:2px
    classDef consumer fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:2px
    classDef uc fill:#F2F2F2,stroke:#E8E8E8,color:#1B3139,stroke-width:1px

    class SANDBOX sandbox
    class DEV,TST dev
    class PROD prod
    class ANALYST analyst
    class CONSUMER consumer
    class C_SBX,C_DEV,C_TST,C_PROD,C_ANA uc
