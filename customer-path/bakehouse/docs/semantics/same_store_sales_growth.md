---
term: Same-Store Sales Growth
synonyms: [comparable sales growth, like-for-like sales, comps]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Gross Sales Revenue, Franchise]
sources: ['https://en.wikipedia.org/wiki/Same-store_sales']
---
## Definition

Sales growth from stores open in both periods, excluding new and closed stores ([Wikipedia](https://en.wikipedia.org/wiki/Same-store_sales)).

## Business context

Separates organic growth from growth through store openings.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises

(current sales of franchises with sales in both periods minus their prior sales) / prior sales. Requires two comparable periods; EDA confirms the date range.
