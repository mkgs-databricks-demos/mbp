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
    EXT["External Customer\nMobile app · Partner API · Web portal"] -->|"API key / OAuth / mTLS"| GW

    subgraph GW["Hyperscaler API Gateway"]
        direction TB
        GW_AUTH["External authentication"]
        GW_RATE["Rate limiting & throttling"]
        GW_IP["IP allowlisting"]
        GW_VAL["Request validation"]
        GW_VER["API versioning"]
        GW_MET["Usage metering"]
    end

    GW -->|"M2M OAuth\nService Principal"| CONSUMER

    subgraph CONSUMER["Databricks Consumer Workspace"]
        direction LR

        subgraph APP_BOX["Databricks App · AppKit"]
            APP_REST["REST API endpoints"]
            APP_LB["Lakebase\nauth + memory"]
        end

        subgraph UGW_BOX["Unity Gateway"]
            UGW_MCP["MCP Services"]
            UGW_GENIE["Genie Agent queries"]
        end

        subgraph MODEL_BOX["Model Serving"]
            MODEL_FM["Foundation Model APIs"]
            MODEL_GOV["Governed by UC ACLs"]
        end
    end

    subgraph SPNS["Three-SPN Architecture"]
        direction LR
        SPN_APP["App SPN\nApp-scoped"]
        SPN_GW["Gateway SPN\nAI-scoped"]
        SPN_EXT["Bootstrap SPN\nMinimal blast radius"]
    end

    classDef ext fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:2px
    classDef gw fill:#FFAB00,stroke:#CC8800,color:#1B3139,stroke-width:2px
    classDef consumer fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:2px
    classDef app fill:#00A972,stroke:#007A52,color:#FFF,stroke-width:1px
    classDef ugw fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:1px
    classDef model fill:#1B3139,stroke:#0F1D22,color:#FFF,stroke-width:1px
    classDef spn fill:#F2F2F2,stroke:#6B7280,color:#1B3139,stroke-width:1px

    class EXT ext
    class GW_AUTH,GW_RATE,GW_IP,GW_VAL,GW_VER,GW_MET gw
    class APP_REST,APP_LB app
    class UGW_MCP,UGW_GENIE ugw
    class MODEL_FM,MODEL_GOV model
    class SPN_APP,SPN_GW,SPN_EXT spn
