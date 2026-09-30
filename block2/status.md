# Project Status: Agentic Capital Allocation Analysis

**Last Updated:** 2026-09-30  
**Current Phase:** Phase 2 Complete — Ready for Phase 3 (Financial Activity & x402)  
**Overall Status:** Phase 1 & Phase 2 Successfully Executed & Documented  

---

## 1. Project Roadmap Overview

| Phase | Milestone | Status | Deliverables |
| :--- | :--- | :---: | :--- |
| **Phase 1** | **ERC-8004 Agent Data Extraction** | 🟢 **Completed** | `erc8004_agents`, `erc8004_events`, Coverage Table |
| **Phase 2** | **Reputation & Feedback History** | 🟢 **Completed** | `erc8004_feedback`, `erc8004_reputation_daily`, spam/anomaly flags |
| **Phase 3** | **Financial Activity & x402 Ingestion** | ⚪ Pending | Pilot validation, `agent_transactions`, `agent_wallet_daily`, `x402_payments` |
| **Phase 4** | **Flow Classification & Dataset Matching** | ⚪ Pending | Matched ERC-8004 <\-> x402, classified financial flows (funding, revenue, A2A, etc.) |
| **Phase 5** | **Validation & Sample Construction** | ⚪ Pending | Manual audit (20 agents, 50 txs), Table 1 Funnel, Percentile distributions |
| **Phase 6** | **Final Synthesis & Reporting** | ⚪ Pending | Clean dataset package, comprehensive data analysis report |

---

## 2. Phase 1 Summary: ERC-8004 Agent Data Extraction

### Core Deliverables Produced
- [x] **Project Structure**:
  - `src/`: modular pipeline code (`erc8004/`, `reputation/`, `finance/`, `x402/`, `classification/`, `validation/`, `utils/`).
  - `data/raw/`: raw archives from HuggingFace (`qntx/erc8004-events`) and Harvard Dataverse (DOI: 10.7910/DVN/HJZW8Q).
  - `data/processed/`: canonical parsed Parquet and CSV files.
  - `results/tables/`: summary statistics and coverage tables.
- [x] **Event Pipeline & Output Files**:
  - `data/processed/erc8004_events.parquet` (and `.csv` preview): **432,404** decoded lifecycle events (Registrations, Mint Transfers, Ownership Transfers, URI Updates, Wallet Updates, Wallet Clears).
  - `data/processed/erc8004_agents.parquet` & `erc8004_agents.csv`: **94,735** unique registered AI agents across Ethereum and Base.
  - `results/tables/coverage_table_phase1.csv` & `results/tables/coverage_table_phase1.md`: Full cross-chain coverage metrics.

### Coverage Table (Phase 1)

| Metric | Ethereum (Chain 1) | Base (Chain 8453) | Total Sample |
| :--- | :---: | :---: | :---: |
| **Total Registered Agents** | 36,359 | 58,376 | **94,735** |
| **Unique Current Owners** | 8,942 | 32,016 | **40,134** |
| **Identified Operating Wallets** | 22,202 (61.06%) | 39,282 (67.29%) | **61,484 (64.90%)** |
| — *High Confidence (On-Chain EIP-712)* | 22,202 | 39,281 | **61,483** |
| — *Medium Confidence (Metadata Declared)* | 0 | 1 | **1** |
| **Agents with Metadata URI** | 18,573 (51.08%) | 39,122 (67.02%) | **57,695 (60.90%)** |
| **Agents with Declared Services** | 292 (0.80%) | 3,561 (6.10%) | **3,853 (4.07%)** |
| **Reputation Coverage (Agents with Feedback)** | 1,656 (4.55%) | 29,325 (50.23%) | **30,981 (32.70%)** |
| **Agents with Ownership Changes** | 11,494 (31.61%) | 18,730 (32.09%) | **30,224 (31.90%)** |
| **Total Ownership Transfer Events** | 14,934 | 18,848 | **33,782** |

### Key Methodology & Architectural Decisions
1. **Wallet Disambiguation Rule**: In strict accordance with the project specification, owner wallets were **never** automatically conflated with operating wallets. Operating wallets were mapped explicitly through on-chain cryptographically signed `setAgentWallet` events (`MetadataSet` with EIP-712 authorization), yielding **61,483 High-Confidence** mappings.
2. **Transfer Lifecycle Reset**: In line with the ERC-8004 smart contract logic (`IdentityRegistryUpgradeable`), token ownership transfers automatically reset the operating wallet unless re-verified by the new owner.
3. **Decoded Data URIs**: Offline decoding of base64 data URIs was implemented, enabling instant zero-latency extraction of agent service cards, tools, and x402 flags.

---

## 3. Phase 2 Summary: Reputation & Feedback History

### Core Deliverables Produced
- [x] `data/processed/erc8004_feedback.parquet` (and `.csv` preview): **356,670** decoded feedback records across Ethereum & Base.
- [x] `data/processed/erc8004_reputation_daily.parquet` (and `.csv` preview): **58,703** agent-day reputation panel observations.
- [x] `results/tables/reputation_summary_phase2.csv` & `results/tables/reputation_summary_phase2.md`: Full anomaly, tag, and distribution report.

### Coverage Table (Phase 2)

| Metric | Ethereum | Base | Total |
| :--- | :---: | :---: | :---: |
| **Total Feedback Events** | 3,182 | 353,488 | **356,670** |
| **Agents with Feedback** | 1,656 | 29,325 | **29,686** (unique) |
| **Unique Feedback Providers** | 632 | 11,514 | **12,109** |
| **Median Feedback Score** | 85.0 | 1.0 | 1.0 |
| **Mean Score (valid scale ≤ 1000)** | 73.71 | 26.61 | **27.03** |
| **Agent Feedbacks p50 / p90 / p99** | 1 / 2 / 15 | 2 / 10 / 20 | 2 / 10 / 21 |
| **Provider Feedbacks p50 / p90 / p99** | 1 / 2 / 22 | 1 / 4 / 31 | 1 / 4 / 30 |
| **Daily Panel (agent-day rows)** | — | — | **58,703** |

### Anomaly & Quality Flags Summary

| Anomaly Flag | Count | Share (%) |
| :--- | :---: | :---: |
| **Self-Feedback** (provider == owner/op wallet) | 79 | 0.02% |
| **Repeated Feedback** (same provider, same agent, >1 time) | 289,049 | 81.04% |
| **Spam Burst** (same provider, same agent, same block) | 54,644 | 15.32% |
| **Concentrated Provider** (>50% share, ≥3 feedbacks) | 62,379 | 17.49% |
| **Extreme Value Outliers** (>1000 or <-100) | 990 | 0.28% |
| **Revoked On-Chain** | 82 | 0.02% |
| **Any Flag** | 301,120 | **84.43%** |

### Top Feedback Categories (tag1)
`miner-vouch` (216,525) · `trust` (36,915) · `trustScore` (10,653) · `contractRisk` (10,648) · `liveness` (9,464) · `starred` (8,875)

### Top Secondary Tags (tag2)
`botcoin` (216,525) · `sentinelnet-v1` (53,217) · `oracle-screening` (36,623) · `liveness-check` (9,359)

### Key Methodology & Decisions
1. **Repeated Feedback Rule**: With 81% of feedback records flagged as repeated, the data strongly indicates a small set of automated rating providers (e.g. `botcoin`, `sentinelnet-v1` oracles). These are preserved in the dataset with flags for downstream filtering, not discarded.
2. **Value Scale Anomalies**: 990 feedback records with values >1,000 (e.g. token-weighted amounts from smart-contract integrations) are flagged as `is_extreme_value_anomaly`. Score statistics are computed on the valid scale subset (≤1,000) to avoid distortion.
3. **Daily Panel Design**: `erc8004_reputation_daily` tracks cumulative `cum_avg_feedback`, `provider_concentration_hhi`, `top_provider_share`, `feedback_dispersion`, and `flagged_feedback_share` per agent per day — ready for Phase 3 & 4 regression-panel construction.

---

## 4. Next Steps (Phase 3)
- Pilot validation: extract and verify financial activity for a 5–10 agent sample.
- Extract full operating wallet transaction histories (ERC-20 / native token inflows & outflows).
- Download and match x402 payment records on Base (USDC).
- Produce `agent_transactions` and `agent_wallet_daily` datasets.

