---
term: Franchise
synonyms: [store, franchise location, outlet, unit]
domain: bakehouse_retail_sales
subdomain: sales
related_terms: [Sales per Franchise, Supplier]
sources: ['https://www.ftc.gov/system/files/documents/plain-language/bus70-franchise-rule-compliance-guide.pdf', 'https://www.franchise.org/franchising-overview/what-is-a-franchise/']
---
## Definition

A business operated under the franchisor's trademark, with significant franchisor control or assistance and a required payment ([FTC](https://www.ftc.gov/system/files/documents/plain-language/bus70-franchise-rule-compliance-guide.pdf)). The franchisee is granted the right to do business under the franchisor's trademark ([IFA](https://www.franchise.org/franchising-overview/what-is-a-franchise/)).

## Business context

Franchise stores are the selling units. Their geography (city, district, country) is the main sales dimension.

## Data usage

Source tables: samples.bakehouse.sales_franchises

Dimension keyed by franchiseID; joins samples.bakehouse.sales_transactions.franchiseID and samples.bakehouse.sales_suppliers.supplierID.

## Values from EDA

values_from_eda: true

Column: sales_franchises.size
