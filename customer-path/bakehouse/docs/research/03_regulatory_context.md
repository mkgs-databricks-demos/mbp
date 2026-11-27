# 03 Regulatory Context — bakehouse_retail_sales

## Summary
The source tables are a Databricks sample dataset used in tutorials, not a regulated production system ([Sample datasets | Databricks](https://docs.databricks.com/aws/en/discover/databricks-datasets); [Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code)), so no regulator mandates its metrics. The data still has the shape of regulated data: a card number column (PCI DSS) and customer contact fields (privacy laws). The models must treat them as sensitive. Franchise financial performance disclosure (FTC Item 19) is context for sales-per-unit metrics, not a requirement on this data.

## Findings

### Payment card data (PCI DSS)
* PCI DSS applies wherever payment card data is stored, processed or transmitted; the current version is v4.0.1, published in the PCI SSC document library ([PCI Security Standards Council: Document Library](https://www.pcisecuritystandards.org/document_library/)).
* `sales_transactions.cardNumber` holds card data; the Databricks bakehouse tutorial drops `cardNumber` from its cleaned transactions table ([Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code)).

### Customer personal data
* Under California law, information that identifies or could reasonably be linked with a consumer is personal information; the CPPA publishes the CCPA/CPRA regulations ([CPPA: CCPA Regulations](https://cppa.ca.gov/regulations/consumer_privacy_act)).
* Under the GDPR, names, email addresses and postal addresses of identifiable persons are personal data ([Regulation (EU) 2016/679 (GDPR), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)).

### Franchise disclosure
* A franchisor that makes financial performance representations must have a reasonable basis and disclose them in Item 19 of the Franchise Disclosure Document ([16 CFR Part 436, govinfo](https://www.govinfo.gov/content/pkg/CFR-2025-title16-vol1/xhtml/CFR-2025-title16-vol1-part436.html); [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide)).

### Mandatory reporting metrics
not found: no regulation mandates specific sales KPIs for this domain.

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| PCI DSS cardholder data | sales_transactions.cardNumber | never a dimension or measure; excluded from metric views and Genie agents; page Cardholder Data |
| Personal information (CCPA/GDPR) | sales_customers.first_name, last_name, email_address, phone_number, address, postal_zip_code | excluded from metric views; only city, state, country, continent (and gender, aggregated) as dimensions |
| FTC Item 19 | sales_transactions.totalPrice, sales_franchises | context for Sales per Franchise (AUV); no constraint on the data |

## Open questions
* Should `gender` be exposed as a dimension at all (aggregated only)? Owner decision.
* Should postal_zip_code be excluded or allowed at aggregate level? Owner decision (default: excluded).

## Sources
1. [Sample datasets | Databricks](https://docs.databricks.com/aws/en/discover/databricks-datasets) — Databricks documentation
2. [Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code) — Databricks documentation
3. [PCI Security Standards Council: Document Library](https://www.pcisecuritystandards.org/document_library/) — PCI SSC (PCI DSS v4.0.1)
4. [CPPA: CCPA Regulations](https://cppa.ca.gov/regulations/consumer_privacy_act) — California Privacy Protection Agency
5. [Regulation (EU) 2016/679 (GDPR), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) — European Union
6. [16 CFR Part 436, govinfo](https://www.govinfo.gov/content/pkg/CFR-2025-title16-vol1/xhtml/CFR-2025-title16-vol1-part436.html) — U.S. GPO, 2025 edition
7. [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide) — Federal Trade Commission
