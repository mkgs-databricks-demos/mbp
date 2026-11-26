# Report: Shipping performance and returns (as produced by Genie)

Persona: fulfillment and quality lead. One Genie conversation (`01f1e9cad66013b3b2aa5140f8ab1e99`), started 2026-11-26T18:54:41Z. Ground truth ran 18:46:07Z-18:46:18Z. Text below is Genie's reply per turn (long replies cut at about 420 characters).

| Turn | Question | Metric view used | Genie answer | Grade |
|---|---|---|---|---|
| 1 | What is the overall on-time shipping rate across all line items? | fulfillment | 49.59%. | correct |
| 2 | Break that down by ship mode. | fulfillment | All 7 modes between 49.54% (AIR) and 49.62% (SHIP). | correct |
| 3 | Which ship mode performs worst? | fulfillment | AIR, 49.54%. | correct |
| 4 | How many line items were received after their commit date? | fulfillment | 18,968,104. | correct |
| 5 | Show those late receipts by ship mode for line items received in 1994. | fulfillment | 7 modes between 410,393 and 412,427; AIR highest at 412,427. | correct |
| 6 | What is the overall return rate as the share of quantity returned? | returns | 24.70%. | correct |
| 7 | Break the return rate down by order priority. | revenue | 24.67%-24.73% by priority; 5-LOW highest. | correct |
| 8 | Same breakdown, but only for orders placed in 1993. | revenue | About 50% for every priority (computed as **returned line count / line count**, then asked whether quantity was wanted). | wrong (basis switched from quantity to line count) |
| 9 | What is the average order fulfillment cycle time in days, from order date to receipt date, per line item? | fulfillment | 76.498 days (about 76.5). | correct |
| 10 | Break the cycle time down by order priority. | fulfillment | About 76.5 days for every priority (76.48-76.51). | correct |

Score: 9 correct, 1 wrong = **90.0%**.

Completeness: 10 of 10 turns answered with data. **Send as-is: no**: the 1993 return-rate cut uses a different basis from the all-years figure two lines above, without saying so in the answer; the numbers happen to be close but are not the requested measure.
