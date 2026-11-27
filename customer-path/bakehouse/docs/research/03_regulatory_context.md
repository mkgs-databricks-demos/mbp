# 03 Regulatory Context — bakehouse_retail_sales

## Summary
The source data is a public, synthetic sample that [simulates a bakery franchise business](https://www.selectdataset.com/dataset/8ce7ecbe16c0a62866e1786c900b085e). No real regulator oversees it, and there are no mandatory reporting metrics. The column shapes still match regulated data in a real deployment, so modeling should follow those rules anyway. Three areas apply: the card number column (PCI DSS v4.0.1), customer personal data (GDPR, CCPA), and franchise unit-level financial figures (FTC Franchise Rule, FDD Item 19). Following the skill's rule for synthetic datasets, the rest of the regulatory search budget went to terminology and KPIs.

## Findings

### Payment card data (PCI DSS v4.0.1)
* The current standard is PCI DSS v4.0.1, published in the [PCI SSC Document Library](https://www.pcisecuritystandards.org/document_library/).
* A stored primary account number (PAN) must be rendered unreadable. The PCI SSC FAQ lists which data elements must be unreadable ([PCI SSC FAQ 1222](https://www.pcisecuritystandards.org/faqs/1222/)).
* Masking controls how a PAN is displayed. Truncation permanently removes digits from a stored PAN. They are different controls ([PCI SSC FAQ 1146](https://www.pcisecuritystandards.org/faqs/1146/); [PCI SSC FAQ 1492](https://www.pcisecuritystandards.org/faqs/1492/)).
* `sales_transactions.cardNumber` is typed `LONG`. From metadata alone, it is not possible to tell whether it holds full, truncated or synthetic numbers.

### Customer personal data (GDPR, CCPA)
* Under GDPR, personal data is any information relating to an identified or identifiable natural person, including identifiers such as a name or location data ([GDPR Article 4(1), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/eng/pdf); [gdpr-info.eu: Personal Data](https://gdpr-info.eu/issues/personal-data/)).
* California's CCPA also defines personal information broadly enough to cover names, email addresses and phone numbers. The statute is published on [California Legislative Information](https://leginfo.legislature.ca.gov/); the exact section URL was not retrieved in this session.
* `sales_customers` holds `first_name`, `last_name`, `email_address`, `phone_number`, `address`, `postal_zip_code` and `gender`. These are direct identifiers or personal attributes.

### Franchise financial performance (FTC Franchise Rule, Item 19)
* When a franchisor makes financial performance representations, such as unit-level sales or AUV, they belong in FDD Item 19 and must have a reasonable basis ([FTC Franchise Rule](https://www.ftc.gov/legal-library/browse/rules/franchise-rule); [FTC Franchise Rule Compliance Guide](https://www.ftc.gov/system/files/documents/plain-language/bus70-franchise-rule-compliance-guide.pdf); [FTC: A Consumer's Guide to Buying a Franchise](https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise)).
* Store-level sales and AUV measures built in this run are internal analytics. Sharing them with prospective franchisees would be an Item 19 matter.

### Required metrics
* None. The dataset is synthetic and no regulator mandates reporting metrics for it ([dataset listing](https://www.selectdataset.com/dataset/8ce7ecbe16c0a62866e1786c900b085e)).

## Relevance to the source tables
| Finding | Table / column | How it is used (measure, dimension, filter, page) |
|---|---|---|
| PCI DSS: PAN must be unreadable when stored | `sales_transactions.cardNumber` | Exclude from metric views and agents. Never a dimension or a filter. If card-level analysis is needed, aggregate only (for example count of distinct cards) |
| GDPR / CCPA personal data | `sales_customers.first_name`, `last_name`, `email_address`, `phone_number`, `address`, `postal_zip_code` | Exclude from metric view dimensions. Use `customerID` for counts and `city` / `state` / `country` / `continent` for geography |
| Personal attribute | `sales_customers.gender` | Aggregate-only dimension, if used at all. Owner to decide |
| FTC Item 19 | Sales per franchise, AUV measures | Label as internal. Glossary page notes the disclosure context |

## Open questions
* Owner: confirm that `cardNumber` should be excluded entirely, even though the data is synthetic.
* Owner: is `gender` allowed as a Genie Agent dimension?
* Do UC column masks or tags apply in the target catalog? This is decided at registration, not in this session.

## Sources
1. [Cookies Dataset DAIS 2024 (Bakehouse dataset listing mirror)](https://www.selectdataset.com/dataset/8ce7ecbe16c0a62866e1786c900b085e) — SelectDataset mirror of the Databricks Marketplace listing
2. [PCI SSC Document Library (PCI DSS v4.0.1)](https://www.pcisecuritystandards.org/document_library/) — PCI Security Standards Council
3. [PCI SSC FAQ 1222](https://www.pcisecuritystandards.org/faqs/1222/) — PCI Security Standards Council
4. [PCI SSC FAQ 1146](https://www.pcisecuritystandards.org/faqs/1146/) — PCI Security Standards Council
5. [PCI SSC FAQ 1492](https://www.pcisecuritystandards.org/faqs/1492/) — PCI Security Standards Council
6. [Regulation (EU) 2016/679 (GDPR), consolidated text](https://eur-lex.europa.eu/eli/reg/2016/679/2016-05-04/eng/pdf) — EUR-Lex, 2016
7. [Personal Data](https://gdpr-info.eu/issues/personal-data/) — gdpr-info.eu
8. [California Legislative Information](https://leginfo.legislature.ca.gov/) — State of California
9. [Franchise Rule](https://www.ftc.gov/legal-library/browse/rules/franchise-rule) — US Federal Trade Commission
10. [Franchise Rule Compliance Guide](https://www.ftc.gov/system/files/documents/plain-language/bus70-franchise-rule-compliance-guide.pdf) — US Federal Trade Commission
11. [A Consumer's Guide to Buying a Franchise](https://www.ftc.gov/business-guidance/resources/consumers-guide-buying-franchise) — US Federal Trade Commission
