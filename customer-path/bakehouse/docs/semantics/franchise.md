---
term: Franchise
synonyms: [franchise location, store, franchise unit, outlet, franchisee]
domain: bakehouse_retail_sales
subdomain: franchise_supply
related_terms: [Sales per Franchise, Bakehouse Supplier, Gross Sales]
sources: ['https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/', 'https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise']
---
## Definition

A location operated by a franchisee, the person or company granted the right to do business under the franchisor's trademark; a location is the site of the franchised operation ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/); [FTC: A Consumer's Guide to Buying a Franchise](https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise)).

## Business context

The franchise is the unit of operational performance: sales, traffic and supplier sourcing are reported per franchise and rolled up by city and country.

## Data usage

Source tables: samples.bakehouse.sales_franchises, samples.bakehouse.sales_transactions

Key `franchiseID` (join sales_transactions.franchiseID = sales_franchises.franchiseID); attributes name, city, district, zipcode, country, size, latitude, longitude, supplierID.

## Values from EDA

values_from_eda: true

Columns: sales_franchises.size (observed size codes are listed by the deep EDA stage).
