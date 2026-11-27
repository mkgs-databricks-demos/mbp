---
term: Sales per Franchise
synonyms: [sales per store, average unit volume, AUV, store productivity]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Gross Sales, Franchise, Comparable Franchise Sales]
sources: ['https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf', 'https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/']
---
## Definition

Total sales divided by the number of stores selling, a store productivity measure ([NielsenIQ: Rate of Sale Metrics](https://training.nielseniq.com/wp-content/uploads/sites/4/2021/06/Rate-of-Sale-Metrics-CIP-Numeric-vs-Weighted.pdf)).

## Business context

Franchisors compare franchises on sales per unit; annualized it is the average unit volume quoted in franchise disclosure documents.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises

sum(totalPrice) / count(DISTINCT franchiseID) for franchises with sales in the period.
