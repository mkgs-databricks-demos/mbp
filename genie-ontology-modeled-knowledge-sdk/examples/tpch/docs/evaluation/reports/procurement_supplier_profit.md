# Report: Supplier profitability and stock value (as produced by Genie)

Persona: procurement lead. One Genie conversation (`01f1e9ca7f04158b9b907c7c68cbf33f`), started 2026-11-26T18:52:14Z. Ground truth ran 18:45:49Z-18:46:05Z. Text below is Genie's reply per turn (long replies cut at about 420 characters).

| Turn | Question | Metric view used | Genie answer | Grade |
|---|---|---|---|---|
| 1 | What is total profit across all years, where profit is revenue minus supply cost? | profit | $706.87B. | correct |
| 2 | Break profit down by supplier region. | none | "I can't answer that ... the profit view has Supplier Nation but not Supplier Region." Offered profit by supplier nation instead. | no_answer |
| 3 | For the most profitable region, show profit by supplier nation. | profit, supply_cost | ASIA; INDIA $29.17B, INDONESIA $28.82B, CHINA $28.11B, VIETNAM $27.99B, JAPAN $27.94B. | correct |
| 4 | Show profit for suppliers in Germany by order year. | profit | 1992 $4.31B ... about $4.28B-$4.31B through 1997, 1998 $2.52B. | correct |
| 5 | What is the total inventory value, supply cost times available quantity, across all part suppliers? | supply_cost | $10.01T. | correct |
| 6 | Break inventory value down by supplier region. | supply_cost | ASIA $2.01T, AMERICA $2.01T, EUROPE $2.01T, MIDDLE EAST $2.00T, AFRICA $1.99T. | correct |
| 7 | Now only suppliers in Germany: which 10 parts have the highest inventory value? | supply_cost | 10 parts, top Part 197009 $20.33M; range $16.86M-$20.33M. | correct |
| 8 | How many suppliers are based in Germany? | supply_cost | 2,003 suppliers (used a partial nation match and asked whether an exact match was wanted). | correct |
| 9 | What is the average unit supply cost for those German suppliers compared with all suppliers? | supply_cost | Germany 500.515406 vs all 500.555561. | correct |
| 10 | What was profit by order year for parts whose name contains 'green'? | profit | 1992 $5.85B ... about $5.8B through 1997, 1998 $3.41B. | correct |

Score: 9 correct, 1 no_answer = **90.0%**.

Completeness: 9 of 10 sections answered. **Send as-is: no**: the profit-by-supplier-region table is missing (turn 3 found the top region anyway, through a second view).
