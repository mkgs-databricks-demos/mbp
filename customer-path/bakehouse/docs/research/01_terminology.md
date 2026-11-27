# 01 Terminology and Domain Overview — bakehouse_retail_sales

## Summary
The domain is retail franchise sales of baked goods: customers buy products at franchise locations, and each franchise sources ingredients from one supplier. The core entities follow standard retail data models (transaction, line item, tender, store, customer) ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)) plus franchising terms (franchisor, franchisee, location, key supplier) ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)). The source tables are a Databricks sample dataset used in Databricks tutorials ([Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code)). Glossary term files for every core term are in `docs/semantics/`.

## Findings

### Retail transaction model
* A retail transaction records business between a store and another party involving the exchange of merchandise or tender, or both; it has sale/return line items and tender line items ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)).
* A tender line item records how the transaction was settled with a valid tender type, i.e. the payment method ([Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf)).
* A Stock-Keeping Unit (SKU) is a system of product identity and pricing ([NIST Handbook 130](https://www.nist.gov/document/00-20-h130-v-final-5pdf)); unit pricing is the cost per unit of measure ([NIST SP 1181 Unit Pricing Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html)).
* Retail sales is the broad sales measure NRF uses in its forecasts ([NRF 2024 Annual Retail Sales Forecast FAQ](https://nrf.com/research-insights/forecasts/nrf-2024-annual-retail-sales-forecast-faq)). Net sales is sales after returns, allowances and discounts; retailers report comparable store sales on net sales ([SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm)).

### Franchising
* Franchisor: the company that grants the franchisee the right to do business under its trademarks; franchisee: the person or company that gets that right; location: the site of the franchised or company-owned operation ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)).
* A franchise gives the franchisee a format or system developed by the franchisor ([FTC: A Consumer's Guide to Buying a Franchise](https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise)).
* Gross revenue (total sales of the business) is generally the basis for royalty fees ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)).
* A key supplier is one with whom the franchisor has negotiated pricing or product availability and whose products are integral to the system ([IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/)); franchisors may control where franchisees buy goods ([FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide)).

### Stakeholders
Franchisor (brand, supplier approval, royalty base), franchisees and store managers (sales, basket, staffing), supply chain (supplier coverage), finance (revenue, payment mix), privacy/security (customer and card data, see `03_regulatory_context.md`).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| Retail transaction | sales_transactions.transactionID, dateTime | count of transactions; time dimension; page Sales Transaction |
| Sale line item | sales_transactions.product, quantity, unitPrice, totalPrice | units and gross sales measures; product dimension |
| Tender / payment method | sales_transactions.paymentMethod | dimension; payment mix measure |
| Cardholder data | sales_transactions.cardNumber | excluded from all models (PCI) |
| Customer | sales_customers (customerID, city, state, country, continent, gender) | customer dimension; personal fields excluded |
| Franchise location | sales_franchises (franchiseID, name, city, district, country, size, latitude, longitude) | store dimension and geography |
| Key / approved supplier | sales_suppliers (supplierID, name, ingredient, approved, continent, city); sales_franchises.supplierID | supplier dimension; supplier coverage |

## Open questions
* Row grain of sales_transactions (one product line per transactionID or one row per transaction): to be confirmed by the deep EDA stage (session 04).
* Currency of unitPrice / totalPrice (integers, no currency column): owner to confirm.
* Meaning of coded values (paymentMethod, franchise and supplier size, approved, gender): deferred to EDA.

## Sources
1. [Oracle Retail Data Model Reference](https://docs.oracle.com/cd/E35214_01/doc.1131/e20361.pdf) — Oracle
2. [NIST Handbook 130](https://www.nist.gov/document/00-20-h130-v-final-5pdf) — NIST, 2020
3. [NIST SP 1181 Unit Pricing Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/1181e2025/NIST.SP.1181e2025.html) — NIST, 2025 edition
4. [NRF 2024 Annual Retail Sales Forecast FAQ](https://nrf.com/research-insights/forecasts/nrf-2024-annual-retail-sales-forecast-faq) — National Retail Federation, 2024
5. [IFA: Common Franchising Terms and Definitions](https://www.franchise.org/franchising-overview/common-franchising-terms-and-definitions/) — International Franchise Association
6. [FTC: A Consumer's Guide to Buying a Franchise](https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise) — Federal Trade Commission
7. [FTC: Franchise Rule Compliance Guide](https://www.ftc.gov/business-guidance/resources/franchise-rule-compliance-guide) — Federal Trade Commission
8. [SEC 10-K filing](https://www.sec.gov/Archives/edgar/data/1051251/000119312506087300/d10k.htm) — U.S. SEC EDGAR, 2006
9. [Databricks: Build a pipeline with Genie Code](https://docs.databricks.com/aws/en/getting-started/starter-journey/build-first-pipeline/genie-code) — Databricks documentation
