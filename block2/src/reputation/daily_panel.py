"""
Agent-Day Daily Reputation Panel Generator
Constructs erc8004_reputation_daily from raw flagged feedback records.
"""

import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any


def build_reputation_daily_panel(df_feedback: pd.DataFrame) -> pd.DataFrame:
    print("Constructing agent-day reputation panel (erc8004_reputation_daily)...")
    
    # Sort chronologically
    df = df_feedback.sort_values(by=["chain", "agent_id", "timestamp_unix"]).reset_index(drop=True)
    
    panel_records = []
    
    # Group by (chain, agent_id)
    grouped = df.groupby(["chain", "chain_id", "agent_id"])
    
    total_groups = len(grouped)
    print(f"Processing {total_groups} unique agent reputation trajectories...")

    for (chain_name, chain_id, aid), group in grouped:
        # Group by date within agent
        date_groups = group.groupby("date")
        
        cum_values: List[float] = []
        provider_counts: Dict[str, int] = {}
        cum_total = 0
        cum_unrevoked = 0
        cum_flagged = 0
        prev_date: Any = None
        
        for dt_str, d_group in date_groups:
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d").date()
            if prev_date is None:
                days_since_prev = 0
            else:
                days_since_prev = (dt_obj - prev_date).days
            prev_date = dt_obj
            
            daily_cnt = len(d_group)
            daily_avg = d_group["normalized_value"].mean()
            
            for row in d_group.itertuples():
                val = row.normalized_value
                cum_values.append(val)
                p_addr = row.provider_wallet.lower()
                provider_counts[p_addr] = provider_counts.get(p_addr, 0) + 1
                cum_total += 1
                if not row.is_revoked:
                    cum_unrevoked += 1
                if row.is_flagged_any:
                    cum_flagged += 1
            
            # Cumulative statistics
            arr_vals = np.array(cum_values, dtype=float)
            cum_avg = float(np.mean(arr_vals))
            dispersion = float(np.std(arr_vals, ddof=1)) if len(arr_vals) > 1 else 0.0
            
            # Share positive / negative
            # Scores >= 50 or > 0 are positive; < 50 or < 0 are negative/poor
            pos_cnt = np.sum(arr_vals > 0)
            neg_cnt = np.sum(arr_vals < 0)
            pos_share = float(pos_cnt / cum_total) if cum_total > 0 else 0.0
            neg_share = float(neg_cnt / cum_total) if cum_total > 0 else 0.0
            
            # Unique providers and concentration HHI
            unique_provs = len(provider_counts)
            counts_arr = np.array(list(provider_counts.values()), dtype=float)
            shares = counts_arr / cum_total
            hhi = float(np.sum(shares ** 2))
            top_prov_share = float(np.max(shares)) if len(shares) > 0 else 0.0
            
            panel_records.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": aid,
                "date": dt_str,
                "daily_feedback_count": daily_cnt,
                "daily_avg_value": round(daily_avg, 4),
                "cum_feedback_count": cum_total,
                "cum_unrevoked_feedback_count": cum_unrevoked,
                "cum_avg_feedback": round(cum_avg, 4),
                "feedback_dispersion": round(dispersion, 4),
                "positive_feedback_share": round(pos_share, 4),
                "negative_feedback_share": round(neg_share, 4),
                "unique_providers": unique_provs,
                "provider_concentration_hhi": round(hhi, 4),
                "top_provider_share": round(top_prov_share, 4),
                "days_since_last_feedback": days_since_prev,
                "cum_flagged_feedback_count": cum_flagged,
                "flagged_feedback_share": round(cum_flagged / cum_total, 4) if cum_total > 0 else 0.0
            })
            
    df_daily = pd.DataFrame(panel_records)
    print(f"Constructed daily panel with {len(df_daily)} agent-day observations.")
    return df_daily
