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

graph LR
    subgraph ACCOUNT["Databricks Account"]
        direction LR

        subgraph USEAST["US-East Region"]
            direction TB
            MA["Metastore A"]
            MA --> CA_DEV["func_dev"]
            MA --> CA_TST["func_tst"]
            MA --> CA_PROD["func · prod"]
            WS_US["Workspaces:\nsandbox · dev · tst/uat\nprod · analyst · consumer"]
        end

        subgraph EUWEST["EU-West Region"]
            direction TB
            MB["Metastore B"]
            MB --> CB_DEV["func_eu_dev"]
            MB --> CB_TST["func_eu_tst"]
            MB --> CB_PROD["func_eu · prod"]
            WS_EU["Workspaces:\neu-dev · eu-prod\neu-consumer"]
        end

        USEAST <-->|"D2D OpenSharing\n(cross-region)"| EUWEST
    end

    classDef metastore fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:2px
    classDef catalog fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:1px
    classDef ws fill:#F2F2F2,stroke:#E8E8E8,color:#1B3139,stroke-width:1px
    classDef region fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:2px

    class MA,MB metastore
    class CA_DEV,CA_TST,CA_PROD,CB_DEV,CB_TST,CB_PROD catalog
    class WS_US,WS_EU ws
