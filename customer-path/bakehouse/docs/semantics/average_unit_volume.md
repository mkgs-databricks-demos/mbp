---
term: Average Unit Volume
synonyms: [AUV, average sales per unit]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Sales per Franchise, Franchise]
sources: ['https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf']
---
## Definition

Average annual sales per store, as reported in industry rankings ([QSR 50](https://www.qsrmagazine.com/wp-content/uploads/2025/07/QSR_QSR50_AUGUST2025.pdf)).

## Business context

The standard franchise benchmark. Disclosing it to prospects is an FDD Item 19 matter.

## Data usage

Source tables: samples.bakehouse.sales_transactions, samples.bakehouse.sales_franchises

Proxy: annualised from the observed window when it is shorter than one year.

sum(totalPrice) / count(distinct franchiseID), scaled to 12 months.
