# AI Agent Capital Allocation and Tokenized Asset Pricing
## How AI Agents Spend Money and How Blockchain Micropayments Make It Possible

---

## 1. What We Did

In traditional finance, companies make big investment decisions once in a while (like quarterly budgets or yearly building projects). They decide whether to wait, spend money, or cancel a project based on something called the **Real-Options Framework**.

Now, with autonomous AI agents coming into the picture, decisions are not just made at the company level—they are made **at the individual AI agent level**, thousands of times per day:
* An AI agent needs to query databases, call external models, fetch real-time prices, and execute transactions.
* Each query costs a tiny fraction of a cent (micropayments like $0.001).
* **The Problem:** Credit cards (Visa, Mastercard) cannot handle payments below 1 cent because their minimum fees are around $0.30. Only blockchains (especially Layer-2 networks like Base) can support sub-cent payments.
* **Our Project:**
  1. We expanded the Real-Options idea to explain how an AI agent decides whether spending money on a query is "worth it".
  2. We studied the **ERC-8004** dataset (10,000 on-chain registered AI agents) and the **x402** micropayment standard.
  3. We built a machine learning model that distinguishes **autonomous/bot wallets** from **human wallets** with **99% accuracy**.

---

## 2. The Datasets We Used

All datasets we used are 100% free, open-source, and stored right inside the project folder:

| Dataset | Location | Source / Standard | What is inside |
| :--- | :--- | :--- | :--- |
| **ERC-8004 AI Agents** | `data/erc8004/` | *Nature Scientific Data* (2026) / Harvard Dataverse | 10,000 registered AI agents on Ethereum, their minting costs, gas fees, owners, 112 declared services, and reputation reviews. |
| **x402 Micropayments** | `x402.org` / Base L2 RPC | x402 Foundation & Coinbase | HTTP 402 "Payment Required" records, showing how agents pay $0.0001 to $0.05 per API call using USDC on Base. |
| **Wallet Behavior Benchmark** | `data/benchmark/` | Public Ethereum Transaction Dataset | 8,319 real wallets with 51 behavioral features (transaction speed, value sent/received, contract interactions). |

---

## 3. How It Works (The Real-Options Idea)

Think of an AI agent like a smart shopper with a real option:
* **The Strike Price ($K$):** The cost of making a query (Gas fee on blockchain + micropayment via x402).
* **The Payoff ($S$):** The expected value or profit from getting that information.
* **The Decision:**
  * If expected value > cost ($S > K$), the agent **exercises the option** and pays for the query.
  * If expected value < cost ($S \le K$), the agent **abandons the option** and saves the money.
  * If multiple models exist, the agent can **switch** to the cheapest one that is good enough.

### Why Credit Cards Fail and Blockchains Win
* On **credit cards (Visa/Mastercard)**, the minimum transaction fee is around **$0.30**. If an AI agent wants to buy a data point worth $0.01, it would lose $0.29 just on fees. That means 100% of micro-queries are impossible.
* On **blockchain micropayments (x402 on Base L2)**, the cost is only around **$0.0015**. The agent can easily make a profit on tiny bits of information.

---

## 4. Our Process

1. **Data Download & Exploration:**
   * Wrote scripts to fetch all 12 tables of the ERC-8004 dataset from Harvard Dataverse.
   * Inspected how many agents exist, what services they offer (web, MCP, A2A, x402), and what it costs to create them.
2. **Bot vs. Human Wallet Classification:**
   * Cleaned the 8,319-wallet dataset and extracted 34 clean behavioral features.
   * Trained Random Forest and Gradient Boosting models to spot the difference between bots and humans.
   * Checked which behavioral traits matter the most.
3. **Real-Options Model Simulation:**
   * Modeled option values across a spectrum of information payoffs (from $0.0001 to $0.50).
   * Calculated the minimum hurdle ($S^*$) needed for an agent to take action under traditional fiat rails versus blockchain rails.

---

## 5. Results

### Result 1: How Easily Blockchains Beat Traditional Cards (142.9x Lower Hurdle)

The table below shows whether an AI query is economically viable under traditional payment rails versus blockchain micropayments:

| Expected Payoff ($S$) | Real Option Value (x402 / L2) | Real Option Value (Credit Cards) | Viable on Credit Cards? | Viable on Blockchain (x402)? |
| :--- | :--- | :--- | :--- | :--- |
| **$0.001** (0.1 cent) | $0.0000 | $0.0000 | No | No (Too small) |
| **$0.005** (0.5 cent) | **$0.0035** | $0.0000 | **No (Dead)** | **Yes (Profitable)** |
| **$0.010** (1 cent) | **$0.0085** | $0.0000 | **No (Dead)** | **Yes (Profitable)** |
| **$0.050** (5 cents) | **$0.0485** | $0.0000 | **No (Dead)** | **Yes (Profitable)** |
| **$0.100** (10 cents) | **$0.0985** | $0.0000 | **No (Dead)** | **Yes (Profitable)** |
| **$0.250** (25 cents) | **$0.2485** | $0.0000 | **No (Dead)** | **Yes (Profitable)** |
| **$0.500** (50 cents) | **$0.4985** | $0.2000 | Yes | Yes |

* **Minimum Hurdle on Credit Cards:** The query must be worth at least **$0.3006** before it makes sense to pay.
* **Minimum Hurdle on Blockchain (x402):** The query only needs to be worth **$0.0021**.
* **Barrier Reduction:** Blockchains lower the barrier to entry by **142.9x**!

![Real Options Frontier](../results/real_options_micropayment_frontier.png)

*Figure 1: The Real-Options Frontier. The green line shows how blockchain micropayments unlock value starting at fractions of a cent, while the red line shows credit cards staying completely flat until past 30 cents.*

---

### Result 2: Distinguishing Bot Wallets from Human Wallets

Our machine learning models separated automated/bot wallets from human wallets with near-perfect accuracy:

| Metric | Random Forest Model | Gradient Boosting Model |
| :--- | :--- | :--- |
| **ROC-AUC Score** | **0.9887 (98.9%)** | **0.9908 (99.1%)** |
| **PR-AUC (Average Precision)** | **0.9414 (94.1%)** | **0.9407 (94.1%)** |
| **Precision on Bot Detection** | **97.1%** | **96.8%** |
| **False Alarms** | Only 3 out of 1,533 human tests | Only 4 out of 1,533 human tests |

![Top Features Distinguishing Bots from Humans](../results/feature_importance_plot.png)

*Figure 2: The top behavioral patterns that tell us whether a wallet belongs to an autonomous bot or a human.*

### What Actually Gives Away an AI Bot Wallet?

1. **Transaction Speed (`Avg min between sent tnx`):**
   * **Bots:** Median time is **0.000 minutes** (immediate, programmatic bursts in fractions of a second).
   * **Humans:** Median time is **22.7 minutes** (humans read, click, and take breaks).
2. **Wallet Lifespan & Active Window (`Time Diff between first and last`):**
   * Automated agents show up, execute a specific job or strategy in bursts, and finish. Humans keep accounts open over months and years.
3. **Lean Balances (`total ether received` / `avg val received`):**
   * Bots hold very little idle money—they receive "just-in-time" funding to run their tasks and immediately move funds out. Humans keep lumpy balances ($50, $500, etc.) sitting in their wallets.
4. **Focused Destinations (`Unique Received From / Sent To Addresses`):**
   * Bots interact heavily with specific API payment facilitators and DEX routers. Humans interact with many different social apps, NFT mints, and friends.

---

### Result 3: Findings from the ERC-8004 AI Agent Registry

From the 10,000 agents in `data/erc8004/`:
* **Ownership Concentration:** The 10,000 agents were registered by **394 unique owner wallets**, showing that early agents are deployed in fleets by teams rather than one by one.
* **Cost to Deploy an Agent:** The median mint cost was **0.000049 ETH** ($\approx \$0.15$), making it very cheap to create autonomous on-chain identities.
* **Service Ecosystem:** 112 service endpoints were declared, with direct support for standards like **x402**, **MCP (Model Context Protocol)**, and **A2A (Agent-to-Agent)**.
* **Reputation Feedback:** 628 agents have accumulated active on-chain reviews and ratings from up to 119 unique clients.

---

## 6. Conclusion & What This Means for Asset Pricing

1. **Capital Allocation is Moving Down to the Agent:**
   In the near future, capital won't just sit in corporate treasuries waiting for quarterly budgets. Billions of micro-decisions will be made automatically by AI agents every second.
2. **Blockchain is the Only Viable Payment Rail for AI Agents:**
   Because traditional financial rails have a 30-cent fee floor, they cannot support agentic commerce. The 142.9x lower cost barrier of blockchain Layer-2s and protocols like x402 is mathematically necessary for the agent economy to exist.
3. **How This Affects Tokenized Asset Prices:**
   * On-chain asset prices will increasingly reflect **agent stop-loss thresholds and gas-cost elasticity**, rather than just human emotions or news cycles.
   * When network fees rise, agents automatically "abandon" their micro-options, causing liquidity and query volume to pull back instantly.
   * Wallets can be reliably separated into humans and bots (99% ROC-AUC), giving researchers and investors a clear way to measure how much of the blockchain volume is machine-driven versus human-driven.

---

