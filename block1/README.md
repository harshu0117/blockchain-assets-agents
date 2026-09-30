# AI Agent Capital Allocation & Tokenized Asset Pricing

This repository investigates autonomous AI agent capital allocation, real-options asset pricing, and on-chain bot vs. human wallet behavioral classification.

---

## Directory Structure

The project has been organized into clear, dedicated directories:

```
blockchain/
├── README.md                                  # Repository overview and guide
├── data/                                      # Datasets and metadata manifests
│   ├── dataverse_files.json                   # Harvard Dataverse file manifest
│   ├── benchmark/                             # Wallet behavior benchmark data
│   │   └── transaction_dataset.csv            # 8,319 Ethereum wallets with 51 behavioral features
│   └── erc8004/                               # 10,000 registered AI agents dataset
│       ├── agents_core.tab
│       ├── agent_feedback_records.tab
│       ├── agent_metadata.tab
│       ├── agent_reputation_summary.tab
│       ├── agent_services.tab
│       ├── crosschain_registrations.tab
│       ├── data dictionary.md
│       ├── data_dictionary_new.tab
│       ├── feedback_issuer_summary.tab
│       ├── metadata_raw_snapshot.jsonl
│       ├── mint_economics.tab
│       └── transfer_history.tab
├── code/                                      # Analysis, modeling, and acquisition scripts
│   ├── requirements.txt                       # Python dependencies
│   ├── download_benchmark.py                  # Fetches the transaction benchmark dataset
│   ├── fetch_dataverse_metadata.py            # Queries Harvard Dataverse API
│   ├── download_dataset.py                    # Downloads all ERC-8004 dataset files
│   ├── inspect_benchmark.py                   # Data inspection and summary statistics
│   ├── eda_erc8004.py                         # Exploratory data analysis of ERC-8004 agents
│   ├── real_options_model.py                  # Real-options asset pricing formulation
│   ├── train_bot_classifier.py                # ML classification (Random Forest & Gradient Boosting)
│   └── test_base_rpc.py                       # Base L2 JSON-RPC connectivity check
├── results/                                   # Generated charts, metrics, and summary tables
│   ├── feature_importances.csv                # Ranked behavioral feature importances
│   ├── feature_importance_plot.png            # Visualization of top bot-discriminating features
│   ├── model_metrics.json                     # ROC-AUC, PR-AUC, and confusion matrix data
│   ├── real_options_micropayment_frontier.png # Real-options barrier comparison plot
│   └── real_options_valuation_table.csv       # Viability table across payoff tiers
└── plans/                                     # Research reports, papers, and presentations
    ├── AGENT_CAPITAL_REAL_OPTIONS_RESEARCH.md # Comprehensive plain-English research report
    ├── AgentCap_RealOptions.pdf               # Academic paper manuscript
    └── Data Analysis - Agentic Capital Allocation.pdf # Presentation and analysis deck
```

---

## Quick Start

### 1. Installation

Install required dependencies:

```bash
pip install -r code/requirements.txt
```

### 2. Running the Pipeline

All scripts can be executed either from the repository root or from within the `code/` folder:

* **Inspect Benchmark Dataset:**
  ```bash
  python code/inspect_benchmark.py
  ```

* **Analyze ERC-8004 Agents & Services:**
  ```bash
  python code/eda_erc8004.py
  ```

* **Run Real-Options Valuation Model:**
  ```bash
  python code/real_options_model.py
  ```

* **Train Bot vs. Human ML Classifier:**
  ```bash
  python code/train_bot_classifier.py
  ```

---

## Key Highlights & Results

1. **Real-Options Hurdle Reduction (142.9x):**
   * Traditional payment rails (Visa/Mastercard) carry a fixed fee floor of ~$0.30, requiring a payoff hurdle of **$0.3006**.
   * Blockchain micropayments (x402 on Base L2) lower the exercise threshold to **$0.0021**, making sub-cent queries viable.

2. **Autonomous Bot Detection (99% ROC-AUC):**
   * Machine learning models differentiate bot wallets from human accounts with **98.9%–99.1% ROC-AUC**.
   * Top distinguishing features include programmatic burst cadence (`Avg min between sent tnx = 0.0`), short active windows, and lean just-in-time balances.
