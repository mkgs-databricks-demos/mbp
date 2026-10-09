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
    USERS["Users / BI / APIs"] --> STABLE["Stable DR Endpoint URL"]

    STABLE --> PRIMARY
    STABLE -.->|failover| SECONDARY

    subgraph PRIMARY["PRIMARY REGION · Active"]
        direction TB
        P_META["Metastore A"]
        P_PROD["Prod workspace"]
        P_CON["Consumer workspace"]
        P_JOBS["Jobs running"]
        P_SQL["SQL active"]
    end

    subgraph SECONDARY["SECONDARY REGION · Standby"]
        direction TB
        S_META["Metastore B"]
        S_DR["DR workspace"]
        S_CON["DR consumer workspace"]
        S_JOBS["Jobs paused"]
        S_SQL["SQL standby"]
    end

    PRIMARY -->|"Managed DR\nor DIY replication"| SECONDARY

    classDef primary fill:#00A972,stroke:#007A52,color:#FFF,stroke-width:2px
    classDef secondary fill:#6B7280,stroke:#4B5563,color:#FFF,stroke-width:2px
    classDef endpoint fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:2px
    classDef user fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:2px

    class USERS user
    class STABLE endpoint
    class P_META,P_PROD,P_CON,P_JOBS,P_SQL primary
    class S_META,S_DR,S_CON,S_JOBS,S_SQL secondary
