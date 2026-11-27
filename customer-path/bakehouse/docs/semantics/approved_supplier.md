---
term: Approved Supplier
synonyms: [approved vendor, certified supplier]
domain: bakehouse_retail_sales
subdomain: franchise_supply
related_terms: [Supplier, Franchise]
sources: ['https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/', 'https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide']
---
## Definition

A supplier the franchisor has approved because its goods meet system quality and uniformity standards; franchisors may require franchisees to buy from approved sources ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/); [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide)).

## Business context

Approval status shows whether franchises source from vetted suppliers, a brand-standard and food-quality control.

## Data usage

Source tables: samples.bakehouse.sales_suppliers

Column `approved` filters suppliers; share approved = count of approved suppliers / count(supplierID).

## Values from EDA

values_from_eda: true

Columns: sales_suppliers.approved (observed codes are listed by the deep EDA stage; meanings are not guessed here).
