# Report: Executive 1997 quarterly review (as produced by Genie)

Persona: VP Supply Chain. One Genie conversation (`01f1e9c9b72a19038c21b8ac2db19861`), started 2026-11-26T18:46:39Z. Ground truth ran 18:45:06Z-18:45:29Z. Text below is Genie's reply per turn (long replies cut at about 420 characters).

| Turn | Question | Metric view used | Genie answer | Grade |
|---|---|---|---|---|
| 1 | What was total revenue for orders placed in 1997? | revenue | Total revenue for orders placed in 1997 was 165246449758.4782. | correct |
| 2 | How does that compare with 1996? Show both years and the percent change. | revenue | Revenue was 165967723990.4606 in 1996 and 165246449758.4782 in 1997. That means 1997 was down 0.43% versus 1996. | correct |
| 3 | Break the 1997 revenue down by customer region. | revenue | ASIA $33.22B, EUROPE $33.10B, MIDDLE EAST $33.07B, AFRICA $32.95B, AMERICA $32.90B. | correct |
| 4 | Which of those regions grew the most in revenue from 1996 to 1997, in percent? | revenue | AFRICA grew the most, with 2.01% growth. | correct |
| 5 | How many orders were placed in 1997? | orders | 1,137,325 orders. | correct |
| 6 | What was the average order value in 1997, as revenue per order? | revenue | $145,293.96. | correct |
| 7 | Show 1997 revenue by quarter. | revenue | Q1 $40.79B, Q2 $41.30B, Q3 $41.61B, Q4 $41.55B; highest in Q3. (Result grid keys quarters as truncated dates.) | correct |
| 8 | Which quarter was the strongest? | revenue | "The strongest quarter in 1997 was 1997-07-01 12:00:00 AM, with revenue of 41.61B." | partial (right value, quarter shown as a timestamp) |
| 9 | What was the on-time shipping rate for line items on orders placed in 1997? | none | "I can't answer that exactly ... the fulfillment view is organized by Ship Date and Receipt Date, not Order Date." | no_answer |
| 10 | And the same rate for 1996? | none | "I can't answer that exactly for the same reason: the fulfillment view does not include Order Date." | no_answer |

Score: 7 correct, 1 partial, 2 no_answer = **75.0%**.

Completeness: 8 of 10 sections answered. **Send as-is: no**: the shipping reliability section is missing (no on-time rate by order year), and the strongest quarter is written as a timestamp.
