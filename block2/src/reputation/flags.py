"""
Anomaly and Quality Flags for ERC-8004 Feedback
Implements detection for:
- Self-feedback (provider == owner or operating wallet)
- Repeated feedback (multiple feedbacks from same provider to same agent)
- Concentrated providers (>50% share of agent's feedbacks)
- Spam burst (multiple feedbacks in the exact same block or tx)
- Revoked feedback
"""

import pandas as pd
import pyarrow.parquet as pq
from typing import Dict, Set


def apply_feedback_flags(df_feedback: pd.DataFrame, agents_pq_path: str = "data/processed/erc8004_agents.parquet") -> pd.DataFrame:
    print("Applying anomaly, spam, and quality flags to feedback records...")
    df = df_feedback.copy()

    # 1. Load agent wallet lookups for self-feedback detection
    agents_df = pq.read_table(agents_pq_path).to_pandas()
    
    # Map (chain, agent_id) -> set of lower-case addresses associated with agent
    agent_wallets_map: Dict[tuple, Set[str]] = {}
    for _, row in agents_df.iterrows():
        key = (row["chain"].lower(), int(row["agent_id"]))
        wallets = set()
        for col in ["initial_owner_wallet", "current_owner_wallet", "operating_wallet"]:
            val = row.get(col)
            if val and pd.notna(val) and isinstance(val, str) and val.startswith("0x"):
                wallets.add(val.lower())
        agent_wallets_map[key] = wallets

    # Flag: Self-Feedback
    def check_self_feedback(row):
        key = (row["chain"].lower(), int(row["agent_id"]))
        agent_wallets = agent_wallets_map.get(key, set())
        return row["provider_wallet"].lower() in agent_wallets

    df["is_self_feedback"] = df.apply(check_self_feedback, axis=1)

    # 2. Flag: Repeated Feedback
    # Sort strictly by block and transaction order
    df = df.sort_values(by=["chain", "agent_id", "provider_wallet", "block_number", "tx_index", "log_index"]).reset_index(drop=True)
    df["provider_agent_feedback_num"] = df.groupby(["chain", "agent_id", "provider_wallet"]).cumcount() + 1
    df["is_repeated_feedback"] = df["provider_agent_feedback_num"] > 1

    # 3. Flag: Spam Burst (multiple feedbacks from same provider in exact same block)
    burst_counts = df.groupby(["chain", "agent_id", "provider_wallet", "block_number"])["feedback_index"].transform("count")
    df["is_spam_burst"] = burst_counts > 1

    # 4. Flag: Concentrated Provider (> 50% share for agents with >= 3 feedbacks)
    total_agent_feedbacks = df.groupby(["chain", "agent_id"])["feedback_index"].transform("count")
    provider_total_feedbacks = df.groupby(["chain", "agent_id", "provider_wallet"])["feedback_index"].transform("count")
    df["provider_share"] = provider_total_feedbacks / total_agent_feedbacks
    df["is_concentrated_provider"] = (total_agent_feedbacks >= 3) & (df["provider_share"] > 0.50)

    # 5. Flag: Extreme Value / Scale Outlier (e.g. test transactions sending max int128 or values > 1000)
    df["is_extreme_value_anomaly"] = (df["normalized_value"] > 1000) | (df["normalized_value"] < -100)

    # 6. Composite flag
    df["is_flagged_any"] = (
        df["is_self_feedback"] |
        df["is_repeated_feedback"] |
        df["is_spam_burst"] |
        df["is_concentrated_provider"] |
        df["is_extreme_value_anomaly"] |
        df["is_revoked"]
    )

    # Re-sort to chronological order
    df = df.sort_values(by=["chain", "block_number", "tx_index", "log_index"]).reset_index(drop=True)

    print("Flags computed:")
    print(f"  Total feedback rows: {len(df)}")
    print(f"  Self-feedback: {df['is_self_feedback'].sum()} ({df['is_self_feedback'].mean()*100:.2f}%)")
    print(f"  Repeated feedback: {df['is_repeated_feedback'].sum()} ({df['is_repeated_feedback'].mean()*100:.2f}%)")
    print(f"  Spam burst: {df['is_spam_burst'].sum()} ({df['is_spam_burst'].mean()*100:.2f}%)")
    print(f"  Concentrated provider: {df['is_concentrated_provider'].sum()} ({df['is_concentrated_provider'].mean()*100:.2f}%)")
    print(f"  Revoked feedback: {df['is_revoked'].sum()} ({df['is_revoked'].mean()*100:.2f}%)")
    print(f"  Any flag: {df['is_flagged_any'].sum()} ({df['is_flagged_any'].mean()*100:.2f}%)")

    return df
