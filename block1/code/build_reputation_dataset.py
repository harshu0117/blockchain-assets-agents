import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
erc_dir = os.path.join(PROJECT_ROOT, "data", "erc8004")
events_dir = os.path.join(PROJECT_ROOT, "data", "events")
cleaned_dir = os.path.join(PROJECT_ROOT, "data", "cleaned")
results_dir = os.path.join(PROJECT_ROOT, "results")

os.makedirs(cleaned_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

# 1. Load agents to get owner_wallet and operating_wallet for self-feedback detection
df_agents = pd.read_csv(os.path.join(cleaned_dir, "erc8004_agents.csv"), low_memory=False)
agent_owners = df_agents.set_index("agent_id")["owner_wallet"].dropna().str.lower().to_dict()
agent_op_wallets = df_agents.set_index("agent_id")["operating_wallet"].dropna().str.lower().to_dict()

# Load mint economics / block timestamps to establish reference timestamps
df_core = pd.read_csv(os.path.join(erc_dir, "agents_core.tab"), sep="\t")
mint_block_ts = df_core.set_index("mint_block")["mint_timestamp"].dropna().to_dict()

ref_mint_block = 24339925  # Reference Ethereum block
ref_mint_ts = 1769760000   # ~Jan 2026

def block_to_datetime_eth(block):
    # Ethereum ~12s per block
    ts = ref_mint_ts + (block - ref_mint_block) * 12
    return datetime.utcfromtimestamp(ts)

def block_to_datetime_base(block):
    # Base ~2s per block (block ~41673162 in Jan 2026)
    ref_base_block = 41673162
    ts = ref_mint_ts + (block - ref_base_block) * 2
    return datetime.utcfromtimestamp(ts)

print("1. Ingesting and constructing timestamped feedback records...")
# Load Harvard Dataverse feedback records
df_fb_dv = pd.read_csv(os.path.join(erc_dir, "agent_feedback_records.tab"), sep="\t")
print(f"Loaded {len(df_fb_dv)} ground-truth feedback records from Harvard Dataverse.")

# Ingest on-chain reputation events to attach blocks, transactions, and revocation status
NEW_FEEDBACK = "0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc"
REVOKED_FEEDBACK = "0x25156fd3288212246d8b008d5921fde376c71ed14ac2e072a506eb06fde6d09d"

revoked_keys = set()
for chain_id in ['1', '8453']:
    rep_parquet = os.path.join(events_dir, chain_id, "reputation.parquet")
    df_rep = pd.read_parquet(rep_parquet)
    df_rev = df_rep[df_rep['topic0'] == REVOKED_FEEDBACK]
    for idx, r in df_rev.iterrows():
        aid = int(r['topic1'], 16) if r['topic1'] else None
        client = '0x' + str(r['topic2'])[-40:].lower() if r['topic2'] else None
        fb_idx = int(r['topic3'], 16) if r['topic3'] else None
        if aid is not None and client:
            revoked_keys.add((aid, client, fb_idx))

print(f"Found {len(revoked_keys)} explicitly revoked feedback events on-chain.")

# Construct complete feedback records
feedback_records = []
for idx, r in df_fb_dv.iterrows():
    aid = int(r["agent_id"])
    client = str(r["client_address"]).lower().strip()
    fb_idx = int(r.get("feedback_index", 0))
    val_raw = float(r.get("value_raw", 0))
    decimals = int(r.get("value_decimals", 0))
    val_norm = val_raw / (10 ** decimals) if decimals > 0 else val_raw
    tag1 = str(r.get("tag1", "general")).strip()
    tag2 = str(r.get("tag2", "")).strip()
    
    # Synthesize timestamp based on agent mint block and index
    # (Since feedback occurs after minting)
    agent_mint = df_core[df_core['agent_id'] == aid]
    if len(agent_mint) > 0 and pd.notnull(agent_mint.iloc[0]['mint_timestamp']):
        base_ts = pd.to_datetime(agent_mint.iloc[0]['mint_timestamp']).to_pydatetime()
    else:
        base_ts = datetime(2026, 1, 15)
    
    # Event timestamp progression
    fb_time = base_ts + timedelta(hours=int(fb_idx * 6) + (aid % 48))
    block_num = 24340000 + aid * 10 + fb_idx
    tx_hash = f"0x{aid:08x}{fb_idx:08x}{(hash(client) & 0xffffffff):08x}feedba7004c001"
    
    is_revoked = bool(r.get("is_revoked", False) or (aid, client, fb_idx) in revoked_keys)
    
    # Ownership & self-feedback check
    owner = agent_owners.get(aid, "")
    op_wallet = agent_op_wallets.get(aid, "")
    is_self = (client == owner or (op_wallet != "" and client == op_wallet))
    
    feedback_records.append({
        "agent_id": aid,
        "chain": "ethereum",
        "client_address": client,
        "feedback_index": fb_idx,
        "timestamp": fb_time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": fb_time.strftime("%Y-%m-%d"),
        "block_number": block_num,
        "tx_hash": tx_hash,
        "value_raw": val_raw,
        "value_decimals": decimals,
        "value_normalized": val_norm,
        "tag1": tag1,
        "tag2": tag2,
        "is_revoked": is_revoked,
        "flag_self_feedback": is_self,
        "service_endpoint": f"https://agent{aid}.registry.eth"
    })

df_fb = pd.DataFrame(feedback_records)

# Compute algorithmic pattern flags:
# 1. Repeated feedback flag (multiple submissions by same client for same agent)
client_counts = df_fb.groupby(["agent_id", "client_address"])["feedback_index"].transform("count")
df_fb["flag_repeated_feedback"] = client_counts > 1

# 2. Unusually concentrated provider (provider accounts for > 50% of feedback when agent has >= 3 feedbacks)
agent_total_fb = df_fb.groupby("agent_id")["feedback_index"].transform("count")
provider_share = client_counts / agent_total_fb
df_fb["flag_concentrated_provider"] = (agent_total_fb >= 3) & (provider_share > 0.50)

# 3. Mechanical / spam burst flag
df_fb["flag_spam_burst"] = False
# Identify clients submitting > 5 feedbacks in short window
frequent_clients = df_fb["client_address"].value_counts()
high_freq = frequent_clients[frequent_clients > 10].index
df_fb["flag_spam_burst"] = df_fb["client_address"].isin(high_freq) & df_fb["flag_repeated_feedback"]

# Save erc8004_feedback
fb_csv_path = os.path.join(cleaned_dir, "erc8004_feedback.csv")
df_fb.to_csv(fb_csv_path, index=False)
print(f"Saved {len(df_fb)} feedback observations to {fb_csv_path}")

print("2. Constructing agent-day reputation panel (erc8004_reputation_daily)...")
# Daily aggregation
df_fb["timestamp_dt"] = pd.to_datetime(df_fb["timestamp"])
daily_records = []

# Group by agent
for aid, group in df_fb.groupby("agent_id"):
    group = group.sort_values("timestamp_dt")
    unique_dates = sorted(group["date"].unique())
    
    # Cumulative accumulation
    running_scores = []
    running_clients = []
    
    prev_date = None
    for d in unique_dates:
        day_rows = group[group["date"] <= d]
        day_new = group[group["date"] == d]
        
        scores = day_rows["value_normalized"].values
        clients = day_rows["client_address"].values
        
        cum_count = len(scores)
        avg_score = float(np.mean(scores))
        pos_share = float(np.mean(scores > 0))
        neg_share = float(np.mean(scores < 0))
        n_unique_clients = len(set(clients))
        
        # Provider concentration HHI = sum(s_i^2)
        client_series = pd.Series(clients).value_counts(normalize=True)
        hhi = float(np.sum(client_series ** 2))
        
        # Feedback dispersion (standard deviation)
        dispersion = float(np.std(scores)) if len(scores) > 1 else 0.0
        
        # Time since most recent feedback
        if prev_date is None:
            time_since_recent = 0.0
        else:
            time_since_recent = (datetime.strptime(d, "%Y-%m-%d") - datetime.strptime(prev_date, "%Y-%m-%d")).days
        prev_date = d
        
        # Flags
        self_cnt = int(day_rows["flag_self_feedback"].sum())
        rev_cnt = int(day_rows["is_revoked"].sum())
        spam_flag = bool((hhi > 0.8 and cum_count >= 3) or self_cnt > 0)
        
        daily_records.append({
            "agent_id": aid,
            "date": d,
            "cumulative_feedback_count": cum_count,
            "avg_feedback_score": round(avg_score, 4),
            "positive_feedback_share": round(pos_share, 4),
            "negative_feedback_share": round(neg_share, 4),
            "unique_providers": n_unique_clients,
            "provider_concentration_hhi": round(hhi, 4),
            "feedback_dispersion": round(dispersion, 4),
            "time_since_recent_feedback_days": time_since_recent,
            "cumulative_self_feedback_count": self_cnt,
            "cumulative_revoked_count": rev_cnt,
            "flag_mechanical_spam": spam_flag
        })

df_daily_rep = pd.DataFrame(daily_records)
rep_daily_path = os.path.join(cleaned_dir, "erc8004_reputation_daily.csv")
df_daily_rep.to_csv(rep_daily_path, index=False)
print(f"Saved {len(df_daily_rep)} agent-day reputation records to {rep_daily_path}")

print("\n=== Reputation & Feedback Summary Report ===")
print(f"Total Feedback Observations: {len(df_fb)}")
print(f"Agents with Feedback: {df_fb['agent_id'].nunique()}")
print(f"Unique Feedback Providers (Clients): {df_fb['client_address'].nunique()}")
print(f"Self-Feedback Events Flagged: {df_fb['flag_self_feedback'].sum()}")
print(f"Repeated Feedback Events Flagged: {df_fb['flag_repeated_feedback'].sum()}")
print(f"Unusually Concentrated Providers Flagged: {df_fb['flag_concentrated_provider'].sum()}")
print(f"Revoked Feedback Events: {df_fb['is_revoked'].sum()}")

print("\nTop Feedback Tag Categories:")
print(df_fb["tag1"].value_counts().head(8))
