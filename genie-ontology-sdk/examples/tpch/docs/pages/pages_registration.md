# TPC-H Glossary -> UC Pages Registration

Source: `examples/tpch/docs/semantics/` (23 term files, parsed with `genie_ontology_sdk.pages.parse_glossary`, 0 parse errors).
Target domain (from term front matter): `tpch_supply_chain` (subdomains `sales`, `fulfillment`, `procurement`).

## Outcome

**Status: blocked. No pages were written.**

* Dry run (`upsert_pages(terms, RestPagesClient(ws), dry_run=True)`, no `domain_id`) ran and made read calls only.
* No Discover domain for TPC-H exists (domain list checked for `tpch` / `supply_chain`; none is `tpch_supply_chain`). Domain creation is out of scope (L100 decision 2), and creating a page needs a `domain_id`.
* Without a domain, title lookup is account-wide: 8 terms match pages with the same title in other, unrelated domains. Updating those pages would overwrite other teams' content, so the live upsert was not run.
* Page writes from an unattended job task also need approval, which this session does not have.
* Idempotency check (second upsert reports 0 changes): not run, because the first live upsert was not run.

## Per-term results (dry run)

| Term | Subdomain | Action | Reason | Description (payload) | Synonyms (payload) |
| --- | --- | --- | --- | --- | --- |
| Average Order Value | sales | failed | several existing pages with this title in other domains (3), none in a TPC-H domain | Revenue divided by number of orders. | AOV, revenue per order |
| Customer | sales | failed | several existing pages with this title in other domains (12), none in a TPC-H domain | A party that places orders with the wholesale supplier. | buyer, account, c_custkey |
| Discount Revenue | sales | failed | no TPC-H domain exists; create needs domain_id | The revenue given up through discounts, `l_extendedprice * l_discount`. | discount amount, forecast revenue change, revenue given away by discounts |
| Extended Price | sales | failed | no TPC-H domain exists; create needs domain_id | The undiscounted price of a line item, generated as `l_quantity * p_retailprice` (truncated at 160 characters) | l_extendedprice, gross price, list price times quantity |
| Gross Charge | sales | failed | no TPC-H domain exists; create needs domain_id | The amount charged to the customer after discount and tax, `l_extendedprice * (1 - l_discount) * (1 + l_tax)`. | sum_charge, charged amount, revenue including tax |
| Inventory Value | procurement | failed | no TPC-H domain exists; create needs domain_id | The cost value of available stock, `sum(ps_supplycost * ps_availqty)`. | stock value, important stock value, available stock value |
| Late Receipt | fulfillment | failed | no TPC-H domain exists; create needs domain_id | A line item the customer received after its committed date (`l_commitdate < l_receiptdate`). | late delivery, received after commit date |
| Line Item | fulfillment | failed | no TPC-H domain exists; create needs domain_id | One line of an order: a quantity of one part from one supplier, with its price, discount, tax, ship, commit and receipt dates (truncated at 160 characters) | order line, lineitem |
| Market Segment | sales | failed | several existing pages with this title in other domains (3), none in a TPC-H domain | The industry segment a customer belongs to. | c_mktsegment, customer segment |
| National Market Share | sales | failed | no TPC-H domain exists; create needs domain_id | The share of revenue volume in a region that a given nation supplies. | market share, mkt_share, nation share of volume |
| On-Time Shipping Rate | fulfillment | failed | no TPC-H domain exists; create needs domain_id | The share of orders delivered on time. | on-time delivery rate, delivery performance, OTD |
| Order Fulfillment Cycle Time | fulfillment | failed | no TPC-H domain exists; create needs domain_id | The elapsed time to fulfill a customer order, from order processing through pick, ship and transit. | order cycle time, lead time, OFCT |
| Order Priority | sales | failed | no TPC-H domain exists; create needs domain_id | The urgency a customer assigns to an order. | o_orderpriority, priority |
| Order Volume | sales | failed | no TPC-H domain exists; create needs domain_id | The number of distinct customer orders in a period. | order count, number of orders |
| Part | procurement | failed | several existing pages with this title in other domains (4), none in a TPC-H domain | A product the wholesaler sells. | product, item, SKU, p_partkey |
| Perfect Order Rate | fulfillment | failed | no TPC-H domain exists; create needs domain_id | The share of orders that meet every delivery expectation: on time, complete, accurately documented and undamaged. | perfect order fulfillment, perfect order performance |
| Profit | procurement | failed | no TPC-H domain exists; create needs domain_id | Revenue minus supply cost per line item, `l_extendedprice * (1 - l_discount) - ps_supplycost * l_quantity`. | product type profit, gross profit, amount |
| Return Flag | fulfillment | failed | no TPC-H domain exists; create needs domain_id | A one-character code on each line item that indicates its return status. | l_returnflag, returned indicator |
| Return Rate | fulfillment | failed | several existing pages with this title in other domains (3), none in a TPC-H domain | The share of shipped product that is returned. | product return rate, returns percentage |
| Revenue | sales | failed | several existing pages with this title in other domains (9), none in a TPC-H domain | The discounted price of line items, `l_extendedprice * (1 - l_discount)`. | net revenue, discounted revenue, sum_disc_price, volume |
| Ship Mode | fulfillment | failed | no TPC-H domain exists; create needs domain_id | The transport method for a line item, for example AIR, RAIL, SHIP, TRUCK or MAIL. | l_shipmode, shipping mode, transport mode |
| Supplier | procurement | failed | several existing pages with this title in other domains (5), none in a TPC-H domain | A company that supplies parts to the wholesaler. | vendor, s_suppkey |
| Supply Cost | procurement | failed | no TPC-H domain exists; create needs domain_id | The supplier's cost for one unit of a part, stored on the part-supplier pairing (`ps_supplycost`) (truncated at 160 characters) | ps_supplycost, supplier cost, unit cost |

Page bodies are not copied here: `to_page_payload(term)` renders them deterministically from each term file (sections Definition, Business context, Data usage, Related terms, Source). New pages are created as `DRAFT` with the caller as owner.

## Owner steps to publish

1. Create (or choose) a Discover domain for TPC-H, for example `tpch_supply_chain`, in the Discover UI. Note its id (`domains/<id>`).
2. Run in a notebook on the `mg-genie-ontology-modeled-knowledge-sdk` checkout (interactive, so page writes can be approved):

```python
import sys
ROOT = "/Workspace/Users/<owner>/mbp/genie-ontology-sdk"
sys.path.insert(0, f"{ROOT}/src")
from databricks.sdk import WorkspaceClient
from genie_ontology_sdk import pages

DOMAIN_ID = "<tpch domain id>"
terms = pages.parse_glossary(f"{ROOT}/examples/tpch/docs/semantics")
client = pages.RestPagesClient(WorkspaceClient())

for dry in (True, False, False):  # dry run, live upsert, idempotency check
    res = pages.upsert_pages(terms, client, dry_run=dry, domain_id=DOMAIN_ID)
    print("dry_run" if dry else "live", {a: sum(r.action == a for r in res) for a in ("create", "update", "unchanged", "error")})
    for r in res:
        if r.action == "error":
            print("  ", r.term, r.error)
```

Expected: the dry run shows 23 `create`; the first live pass creates 23 pages; the third pass reports 23 `unchanged`. Passing `domain_id` scopes the title lookup to that domain, so the pages in other domains are not matched. A domain-filtered list needs domain admin rights.
