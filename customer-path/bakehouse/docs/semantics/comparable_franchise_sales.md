---
term: Comparable Franchise Sales
synonyms: [same-store sales, comparable store sales, like-for-like sales, comp sales]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Sales per Franchise, Gross Sales, Franchise]
sources: ['https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm', 'https://investor.tjx.com/node/19916/html']
---
## Definition

The year-over-year change in net sales at stores open at least twelve months ([SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm)); some retailers require two fiscal years of operation ([TJX SEC filing](https://investor.tjx.com/node/19916/html)).

## Business context

Comparable sales separate growth from existing units from growth from new units; it is the main retail growth KPI.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises

Proxy: franchises with sales in both the current and the prior period, not stores open 12 months (no opening date); gross, not net, sales.

(sum(totalPrice) current period - sum(totalPrice) prior period) / sum(totalPrice) prior period, over franchiseIDs present in both periods. Needs a data span longer than one comparison period (checked by EDA).
