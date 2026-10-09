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
    subgraph GLOBAL["Global Databricks Account"]
        direction TB

        subgraph US["US-East"]
            US_M["Metastore A"]
            US_WS["Prod · Consumer · Analyst\nDev · Tst · Sandbox"]
        end

        subgraph EU["EU-West"]
            EU_M["Metastore B"]
            EU_WS["Prod · Consumer\nAnalyst · Dev"]
        end

        subgraph APAC["APAC · Sydney"]
            AP_M["Metastore C"]
            AP_WS["Prod · Consumer"]
        end

        US <-->|"D2D OpenSharing"| EU
        EU <-->|"D2D OpenSharing"| APAC
        US <-->|"D2D OpenSharing"| APAC
    end

    US_DR["US-West\nDR Secondary"] -.->|"Managed DR"| US
    EU_DR["EU-North\nDR Secondary"] -.->|"Managed DR"| EU

    NOTE["Data Sovereignty:\nEU data stays in EU metastore\nGDPR enforced at catalog binding level"]

    classDef region fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:2px
    classDef dr fill:#6B7280,stroke:#4B5563,color:#FFF,stroke-width:1px
    classDef note fill:#FFAB00,stroke:#CC8800,color:#1B3139,stroke-width:1px
    classDef meta fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:2px
    classDef ws fill:#F2F2F2,stroke:#E8E8E8,color:#1B3139,stroke-width:1px

    class US_M,EU_M,AP_M meta
    class US_WS,EU_WS,AP_WS ws
    class US_DR,EU_DR dr
    class NOTE note
