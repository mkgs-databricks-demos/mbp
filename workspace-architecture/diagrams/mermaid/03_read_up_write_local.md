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

graph BT
    subgraph HIERARCHY["Read Up, Write Local — Access Hierarchy"]
        direction BT

        DEV_CAT["func_dev\nDEV catalog"]
        TST_CAT["func_tst\nTEST catalog"]
        PROD_CAT["func · PROD catalog\nSource of Truth"]

        DEV_CAT -->|"READ by Dev WS"| TST_CAT
        TST_CAT -->|"READ by Dev WS, Tst WS"| PROD_CAT

        DEV_WS["Dev WS\nWRITE: func_dev\nREAD: func_tst, func"]
        TST_WS["Tst/UAT WS\nWRITE: func_tst\nREAD: func"]
        PROD_WS["Prod WS\nWRITE: func\nTop of hierarchy"]
        ANA_WS["Analyst WS\nWRITE: analyst_cat\nREAD: func"]
        CON_WS["Consumer WS\nNo write\nREAD: func gold"]
    end

    DEV_WS -.->|writes| DEV_CAT
    TST_WS -.->|writes| TST_CAT
    PROD_WS -.->|writes| PROD_CAT
    ANA_WS -.->|reads| PROD_CAT
    CON_WS -.->|reads| PROD_CAT

    classDef prodCat fill:#FF3621,stroke:#CC2B1A,color:#FFF,stroke-width:3px
    classDef lowerCat fill:#077A9D,stroke:#055F7A,color:#FFF,stroke-width:2px
    classDef ws fill:#F2F2F2,stroke:#1B3139,color:#1B3139,stroke-width:1px

    class PROD_CAT prodCat
    class DEV_CAT,TST_CAT lowerCat
    class DEV_WS,TST_WS,PROD_WS,ANA_WS,CON_WS ws
