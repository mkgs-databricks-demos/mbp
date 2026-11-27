---
term: Gross Sales
synonyms: [revenue, sales revenue, total sales, sales]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Net Sales, Sales Transaction, Average Transaction Value, Sales per Franchise]
sources: ['https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/', 'https://nrf.com/research-insights/forecasts/nrf-2024-annual-retail-sales-forecast-faq']
---
## Definition

Total sales of the business before deductions; franchise systems use gross revenue as the usual basis for royalty calculations ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)).

## Business context

Gross sales is the headline revenue figure for each franchise, city, country and product, and the basis for royalty reporting in franchising.

## Data usage

Source tables: samples.bakehouse.sales_transactions

sum(totalPrice) over transaction rows, any period. The data has no discount or return columns, so this is gross, not net, sales.
