"""
Phase 2 Reputation Pipeline Orchestrator
Executes:
1. Decoding raw NewFeedback, FeedbackRevoked, and ResponseAppended events
2. Applying quality, spam, self-feedback, and anomaly flags
3. Building agent-day daily reputation panel (erc8004_reputation_daily)
4. Producing comprehensive Phase 2 summary metrics and tables
"""

import os
import pandas as pd
import numpy as np

from src.reputation.feedback_decoder import decode_chain_reputation
from src.reputation.flags import apply_feedback_flags
from src.reputation.daily_panel import build_reputation_daily_panel


def run_reputation_pipeline():
    print("=" * 60)
    print("Starting Phase 2 Reputation & Feedback Pipeline")
    print("=" * 60)

    # 1. Decode events across chains
    chain_dfs = []
    for chain_id in [1, 8453]:
        df_chain, _, _ = decode_chain_reputation(chain_id)
        chain_dfs.append(df_chain)

    df_feedback = pd.concat(chain_dfs, ignore_index=True)
    print(f"Total raw feedback records collected: {len(df_feedback)}")

    # 2. Apply anomaly and quality flags
    df_feedback_flagged = apply_feedback_flags(df_feedback)

    # 3. Save erc8004_feedback
    os.makedirs("data/processed", exist_ok=True)
    fb_pq_path = "data/processed/erc8004_feedback.parquet"
    fb_csv_path = "data/processed/erc8004_feedback.csv"
    df_feedback_flagged.to_parquet(fb_pq_path, index=False)
    # Save preview sample to CSV
    df_feedback_flagged.head(10000).to_csv(fb_csv_path, index=False)
    print(f"Saved {len(df_feedback_flagged)} feedback records to {fb_pq_path} and preview to {fb_csv_path}")

    # 4. Construct daily panel
    df_daily = build_reputation_daily_panel(df_feedback_flagged)
    daily_pq_path = "data/processed/erc8004_reputation_daily.parquet"
    daily_csv_path = "data/processed/erc8004_reputation_daily.csv"
    df_daily.to_parquet(daily_pq_path, index=False)
    df_daily.head(10000).to_csv(daily_csv_path, index=False)
    print(f"Saved {len(df_daily)} daily panel rows to {daily_pq_path} and preview to {daily_csv_path}")

    # 5. Generate Section 3 Summary Report
    os.makedirs("results/tables", exist_ok=True)
    
    summary_metrics = []
    for chain_name in ["ethereum", "base", "total"]:
        if chain_name == "total":
            sub_fb = df_feedback_flagged
            sub_daily = df_daily
        else:
            sub_fb = df_feedback_flagged[df_feedback_flagged["chain"] == chain_name]
            sub_daily = df_daily[df_daily["chain"] == chain_name]

        total_obs = len(sub_fb)
        agents_with_fb = sub_fb["agent_id"].nunique()
        unique_providers = sub_fb["provider_wallet"].str.lower().nunique()
        self_fb = sub_fb["is_self_feedback"].sum()
        repeated_fb = sub_fb["is_repeated_feedback"].sum()
        spam_burst = sub_fb["is_spam_burst"].sum()
        conc_prov = sub_fb["is_concentrated_provider"].sum()
        revoked_fb = sub_fb["is_revoked"].sum()
        has_resp = sub_fb["has_response"].sum()
        extreme_vals = sub_fb["is_extreme_value_anomaly"].sum()
        any_flag = sub_fb["is_flagged_any"].sum()
        
        valid_scale_mask = (sub_fb["normalized_value"] >= -100) & (sub_fb["normalized_value"] <= 1000)
        avg_score_valid = sub_fb[valid_scale_mask]["normalized_value"].mean()
        median_score = sub_fb["normalized_value"].median()

        # Distribution of feedbacks per agent
        agent_counts = sub_fb.groupby("agent_id").size()
        ap10 = np.percentile(agent_counts, 10) if len(agent_counts) else 0
        ap25 = np.percentile(agent_counts, 25) if len(agent_counts) else 0
        ap50 = np.percentile(agent_counts, 50) if len(agent_counts) else 0
        ap75 = np.percentile(agent_counts, 75) if len(agent_counts) else 0
        ap90 = np.percentile(agent_counts, 90) if len(agent_counts) else 0
        ap99 = np.percentile(agent_counts, 99) if len(agent_counts) else 0

        # Distribution of feedbacks per provider
        prov_counts = sub_fb.groupby("provider_wallet").size()
        pp10 = np.percentile(prov_counts, 10) if len(prov_counts) else 0
        pp25 = np.percentile(prov_counts, 25) if len(prov_counts) else 0
        pp50 = np.percentile(prov_counts, 50) if len(prov_counts) else 0
        pp75 = np.percentile(prov_counts, 75) if len(prov_counts) else 0
        pp90 = np.percentile(prov_counts, 90) if len(prov_counts) else 0
        pp99 = np.percentile(prov_counts, 99) if len(prov_counts) else 0

        summary_metrics.append({
            "Chain": chain_name.capitalize(),
            "Total Feedback Events": total_obs,
            "Agents with Feedback": agents_with_fb,
            "Unique Providers": unique_providers,
            "Median Feedback Score": round(median_score, 2),
            "Mean Feedback Score (Scale <= 1000)": round(avg_score_valid, 2),
            "Extreme Value Anomalies": extreme_vals,
            "Self-Feedback Count": self_fb,
            "Self-Feedback (%)": round(100.0 * self_fb / total_obs, 2) if total_obs else 0.0,
            "Repeated Feedback Count": repeated_fb,
            "Repeated Feedback (%)": round(100.0 * repeated_fb / total_obs, 2) if total_obs else 0.0,
            "Spam Bursts (Same Block)": spam_burst,
            "Concentrated Providers": conc_prov,
            "Revoked Feedbacks": revoked_fb,
            "Responses Appended": has_resp,
            "Flagged Any Anomaly": any_flag,
            "Flagged Share (%)": round(100.0 * any_flag / total_obs, 2) if total_obs else 0.0,
            "Agent Feedbacks p50": ap50,
            "Agent Feedbacks p90": ap90,
            "Agent Feedbacks p99": ap99,
            "Provider Feedbacks p50": pp50,
            "Provider Feedbacks p90": pp90,
            "Provider Feedbacks p99": pp99,
        })

    df_summary = pd.DataFrame(summary_metrics)
    summary_csv_path = "results/tables/reputation_summary_phase2.csv"
    summary_md_path = "results/tables/reputation_summary_phase2.md"
    df_summary.to_csv(summary_csv_path, index=False)

    # Top tags analysis
    tag1_counts = df_feedback_flagged[df_feedback_flagged["tag1"] != ""]["tag1"].value_counts().head(10)
    tag2_counts = df_feedback_flagged[df_feedback_flagged["tag2"] != ""]["tag2"].value_counts().head(10)

    # Write Markdown Report
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# ERC-8004 Reputation & Feedback Summary Report (Phase 2)\n\n")
        f.write("## 1. Overall Reputation Statistics by Chain\n\n")
        f.write(df_summary.to_markdown(index=False))
        f.write("\n\n## 2. Top Feedback Tags & Categories\n\n")
        f.write("### Primary Category Tag (tag1)\n\n")
        f.write(tag1_counts.to_frame("Count").to_markdown())
        f.write("\n\n### Secondary Category Tag (tag2)\n\n")
        f.write(tag2_counts.to_frame("Count").to_markdown())
        f.write("\n\n## 3. Anomaly and Spam Detection Highlights\n\n")
        f.write(f"- **Self-Feedback:** Detected {df_feedback_flagged['is_self_feedback'].sum():,} feedback records originating from the agent's own owner or operating wallet.\n")
        f.write(f"- **Repeated Feedbacks:** {df_feedback_flagged['is_repeated_feedback'].sum():,} feedbacks where a single provider rated the same agent multiple times.\n")
        f.write(f"- **Spam Bursts:** {df_feedback_flagged['is_spam_burst'].sum():,} feedbacks submitted in rapid bursts within the exact same block.\n")
        f.write(f"- **Extreme Value Outliers:** {df_feedback_flagged['is_extreme_value_anomaly'].sum():,} feedbacks containing test or out-of-scale values (>1000 or <-100).\n")
        f.write(f"- **Revocations:** {df_feedback_flagged['is_revoked'].sum():,} feedback events formally revoked on-chain.\n")
        f.write(f"- **Responses:** {df_feedback_flagged['has_response'].sum():,} feedbacks received an on-chain response from the agent.\n")

    print("\nPhase 2 Summary Table:")
    print(df_summary.to_string())
    print(f"\nSaved reputation summary report to {summary_md_path}")
    print("Phase 2 Pipeline execution completed successfully!")


if __name__ == "__main__":
    run_reputation_pipeline()
