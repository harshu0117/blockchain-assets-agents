# ERC-8004 Reputation & Feedback Summary Report (Phase 2)

## 1. Overall Reputation Statistics by Chain

| Chain    |   Total Feedback Events |   Agents with Feedback |   Unique Providers |   Median Feedback Score |   Mean Feedback Score (Scale <= 1000) |   Extreme Value Anomalies |   Self-Feedback Count |   Self-Feedback (%) |   Repeated Feedback Count |   Repeated Feedback (%) |   Spam Bursts (Same Block) |   Concentrated Providers |   Revoked Feedbacks |   Responses Appended |   Flagged Any Anomaly |   Flagged Share (%) |   Agent Feedbacks p50 |   Agent Feedbacks p90 |   Agent Feedbacks p99 |   Provider Feedbacks p50 |   Provider Feedbacks p90 |   Provider Feedbacks p99 |
|:---------|------------------------:|-----------------------:|-------------------:|------------------------:|--------------------------------------:|--------------------------:|----------------------:|--------------------:|--------------------------:|------------------------:|---------------------------:|-------------------------:|--------------------:|---------------------:|----------------------:|--------------------:|----------------------:|----------------------:|----------------------:|-------------------------:|-------------------------:|-------------------------:|
| Ethereum |                    3182 |                   1656 |                632 |                      85 |                                 73.71 |                         0 |                     1 |                0.03 |                       581 |                   18.26 |                        130 |                      255 |                   0 |                   37 |                   676 |               21.24 |                     1 |                     2 |                 15.45 |                        1 |                        2 |                    21.97 |
| Base     |                  353488 |                  29325 |              11514 |                       1 |                                 26.61 |                       990 |                    78 |                0.02 |                    288468 |                   81.61 |                      54514 |                    62124 |                  82 |                 4489 |                300444 |               84.99 |                     2 |                    10 |                 20    |                        1 |                        4 |                    30.87 |
| Total    |                  356670 |                  29686 |              12109 |                       1 |                                 27.03 |                       990 |                    79 |                0.02 |                    289049 |                   81.04 |                      54644 |                    62379 |                  82 |                 4526 |                301120 |               84.43 |                     2 |                    10 |                 21    |                        1 |                        4 |                    30    |

## 2. Top Feedback Tags & Categories

### Primary Category Tag (tag1)

| tag1         |   Count |
|:-------------|--------:|
| miner-vouch  |  216525 |
| trust        |   36915 |
| trustScore   |   10653 |
| contractRisk |   10648 |
| counterparty |   10643 |
| activity     |   10641 |
| longevity    |   10635 |
| liveness     |    9464 |
| starred      |    8875 |
| tip          |    4336 |

### Secondary Category Tag (tag2)

| tag2             |   Count |
|:-----------------|--------:|
| botcoin          |  216525 |
| sentinelnet-v1   |   53217 |
| oracle-screening |   36623 |
| liveness-check   |    9359 |
| agent            |    4352 |
| agent-identity   |    1460 |
| mint             |    1165 |
| trust            |    1087 |
| perfect          |    1019 |
| zk-verified      |     913 |

## 3. Anomaly and Spam Detection Highlights

- **Self-Feedback:** Detected 79 feedback records originating from the agent's own owner or operating wallet.
- **Repeated Feedbacks:** 289,049 feedbacks where a single provider rated the same agent multiple times.
- **Spam Bursts:** 54,644 feedbacks submitted in rapid bursts within the exact same block.
- **Extreme Value Outliers:** 990 feedbacks containing test or out-of-scale values (>1000 or <-100).
- **Revocations:** 82 feedback events formally revoked on-chain.
- **Responses:** 4,526 feedbacks received an on-chain response from the agent.
