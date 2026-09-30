import os
import json
import re
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")
erc_dir = os.path.join(PROJECT_ROOT, "data", "erc8004")
cleaned_dir = os.path.join(PROJECT_ROOT, "data", "cleaned")
results_dir = os.path.join(PROJECT_ROOT, "results")

os.makedirs(cleaned_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

REGISTERED_TOPIC = "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
METADATA_SET_TOPIC = "0x2c149ed548c6d2993cd73efe187df6eccabe4538091b33adbd25fafdb8a1468b"
URI_UPDATED_TOPIC = "0x3a2c7fffc2cba7582c690e3b82c453ea02a308326a98a3ad7576c606336409fb"

print("1. Processing Harvard Dataverse metadata & operating wallets...")
# Extract operating wallets from metadata_raw_snapshot.jsonl
agent_operating_wallets = {}
with open(os.path.join(erc_dir, "metadata_raw_snapshot.jsonl"), "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        aid = item.get("agent_id")
        raw_text = item.get("raw_text", "")
        if not raw_text:
            continue
        try:
            parsed = json.loads(raw_text)
            wallets = parsed.get("wallets", {})
            if isinstance(wallets, dict):
                # Search for base/evm/x402/acp wallet addresses
                base_wallet = None
                if "x402" in wallets and isinstance(wallets["x402"], dict):
                    base_wallet = wallets["x402"].get("base") or wallets["x402"].get("evm")
                if not base_wallet and "acp" in wallets and isinstance(wallets["acp"], dict):
                    base_wallet = wallets["acp"].get("base") or wallets["acp"].get("evm")
                if not base_wallet and "base" in wallets:
                    base_wallet = wallets.get("base")
                if not base_wallet and "evm" in wallets:
                    base_wallet = wallets.get("evm")
                
                if base_wallet and re.match(r"^0x[a-fA-F0-9]{40}$", str(base_wallet)):
                    agent_operating_wallets[aid] = {
                        "operating_wallet": base_wallet.lower(),
                        "wallet_source": "metadata_wallets_json",
                        "wallet_confidence": "high",
                        "service_ecosystem": list(wallets.keys())
                    }
        except Exception:
            pass

# Also check agent_services endpoints for EVM addresses if not already matched
df_serv = pd.read_csv(os.path.join(erc_dir, "agent_services.tab"), sep="\t")
for idx, r in df_serv.iterrows():
    aid = r["agent_id"]
    if aid not in agent_operating_wallets:
        ep = str(r.get("endpoint", ""))
        addrs = re.findall(r"0x[a-fA-F0-9]{40}", ep)
        # Avoid contract registries
        valid_addrs = [a.lower() for a in addrs if a.lower() not in [
            "0x8004a169fb4a3325136eb29fa0ceb6d2e539a432",
            "0x8004a818bfb912233c491871b3d84c89a494bd9e"
        ]]
        if valid_addrs:
            agent_operating_wallets[aid] = {
                "operating_wallet": valid_addrs[0],
                "wallet_source": "service_endpoint_address",
                "wallet_confidence": "medium",
                "service_ecosystem": [str(r.get("service_name"))]
            }

print(f"Identified operating wallets for {len(agent_operating_wallets)} agents.")

# Ingest Harvard Dataverse core agents
df_core_dv = pd.read_csv(os.path.join(erc_dir, "agents_core.tab"), sep="\t")
df_meta_dv = pd.read_csv(os.path.join(erc_dir, "agent_metadata.tab"), sep="\t")
meta_dict = df_meta_dv.set_index("agent_id").to_dict(orient="index")
service_counts = df_serv.groupby("agent_id")["service_name"].count().to_dict()

# Load reputation feedback counts from Harvard Dataverse
df_rep_dv = pd.read_csv(os.path.join(erc_dir, "agent_reputation_summary.tab"), sep="\t")
rep_counts_dv = df_rep_dv.set_index("agent_id")["feedback_count_total"].to_dict()

print("2. Parsing on-chain identity & transfer events for Ethereum (1) and Base (8453)...")
all_events = []
all_agents = []

chain_names = {"1": "ethereum", "8453": "base"}

for chain_id, chain_name in chain_names.items():
    print(f"Processing chain: {chain_name} (ID {chain_id})...")
    id_parquet_path = os.path.join(events_dir, chain_id, "identity.parquet")
    df_id = pd.read_parquet(id_parquet_path)
    
    # Filter out removed logs
    if "removed" in df_id.columns:
        df_id = df_id[~df_id["removed"]]
    
    # 1. Registered events
    df_reg = df_id[df_id["topic0"] == REGISTERED_TOPIC]
    print(f" - Found {len(df_reg)} Registered events")
    
    # 2. Transfer events
    df_tr = df_id[df_id["topic0"] == TRANSFER_TOPIC]
    print(f" - Found {len(df_tr)} Transfer events")
    
    # Track agent registrations and transfers
    agent_reg_info = {}
    for idx, r in df_reg.iterrows():
        aid = int(r["topic1"], 16) if r["topic1"] else None
        if aid is None:
            continue
        owner = "0x" + str(r["topic2"])[-40:].lower() if r["topic2"] else None
        if aid not in agent_reg_info:
            agent_reg_info[aid] = {
                "agent_id": aid,
                "chain": chain_name,
                "registration_block": int(r["block_number"]),
                "registration_tx": str(r["tx_hash"]),
                "original_owner": owner,
                "current_owner": owner,
                "transfer_count": 0,
                "first_block": int(r["block_number"]),
                "last_block": int(r["block_number"])
            }
        all_events.append({
            "chain": chain_name,
            "agent_id": aid,
            "event_type": "Registered",
            "block_number": int(r["block_number"]),
            "tx_hash": str(r["tx_hash"]),
            "from_address": "0x0000000000000000000000000000000000000000",
            "to_address": owner,
            "details": "Initial Agent Identity Registration"
        })
    
    # Process transfers to get time-varying and latest ownership
    # Sort transfers chronologically
    df_tr_sorted = df_tr.sort_values(by=["block_number", "log_index"])
    for idx, r in df_tr_sorted.iterrows():
        aid = int(r["topic3"], 16) if r["topic3"] else None
        if aid is None:
            continue
        from_w = "0x" + str(r["topic1"])[-40:].lower() if r["topic1"] else None
        to_w = "0x" + str(r["topic2"])[-40:].lower() if r["topic2"] else None
        
        is_mint = (from_w == "0x0000000000000000000000000000000000000000")
        
        if aid in agent_reg_info:
            agent_reg_info[aid]["last_block"] = max(agent_reg_info[aid]["last_block"], int(r["block_number"]))
            if not is_mint:
                agent_reg_info[aid]["current_owner"] = to_w
                agent_reg_info[aid]["transfer_count"] += 1
        else:
            # If agent registered before parquet archive window
            agent_reg_info[aid] = {
                "agent_id": aid,
                "chain": chain_name,
                "registration_block": int(r["block_number"]),
                "registration_tx": str(r["tx_hash"]),
                "original_owner": to_w,
                "current_owner": to_w,
                "transfer_count": 0 if is_mint else 1,
                "first_block": int(r["block_number"]),
                "last_block": int(r["block_number"])
            }
            
        all_events.append({
            "chain": chain_name,
            "agent_id": aid,
            "event_type": "Mint" if is_mint else "Transfer",
            "block_number": int(r["block_number"]),
            "tx_hash": str(r["tx_hash"]),
            "from_address": from_w,
            "to_address": to_w,
            "details": f"Token Transfer from {from_w} to {to_w}"
        })
        
    for aid, info in agent_reg_info.items():
        # Match metadata if available (for Ethereum Harvard Dataverse sample)
        meta = meta_dict.get(aid, {})
        serv_cnt = service_counts.get(aid, 0)
        rep_fb_cnt = rep_counts_dv.get(aid, 0)
        
        # Check operating wallet
        op_info = agent_operating_wallets.get(aid, {})
        op_wallet = op_info.get("operating_wallet")
        op_src = op_info.get("wallet_source", "none")
        op_conf = op_info.get("wallet_confidence", "none")
        
        all_agents.append({
            "agent_id": aid,
            "chain": chain_name,
            "registration_block": info["registration_block"],
            "registration_tx": info["registration_tx"],
            "owner_wallet": info["current_owner"],
            "operating_wallet": op_wallet,
            "wallet_source": op_src,
            "wallet_confidence": op_conf,
            "transfer_count": info["transfer_count"],
            "name": meta.get("name", f"Agent #{aid}"),
            "description": meta.get("description", ""),
            "metadata_hosting_type": meta.get("metadata_content_type", "unknown"),
            "service_count": serv_cnt,
            "x402_support": bool(meta.get("x402_support", False) or op_wallet is not None),
            "reputation_feedback_count": rep_fb_cnt,
            "active": bool(meta.get("active", True))
        })

df_all_agents = pd.DataFrame(all_agents)
df_all_events = pd.DataFrame(all_events)

# Sort agents by chain and agent_id
df_all_agents = df_all_agents.sort_values(by=["chain", "agent_id"]).reset_index(drop=True)
df_all_events = df_all_events.sort_values(by=["chain", "block_number"]).reset_index(drop=True)

# Save cleaned files
agents_csv_path = os.path.join(cleaned_dir, "erc8004_agents.csv")
events_csv_path = os.path.join(cleaned_dir, "erc8004_events.csv")
df_all_agents.to_csv(agents_csv_path, index=False)
df_all_events.to_csv(events_csv_path, index=False)

print(f"\nSaved {len(df_all_agents)} agents to {agents_csv_path}")
print(f"Saved {len(df_all_events)} events to {events_csv_path}")

print("3. Generating Chain Coverage Table...")
# Section 2 Coverage Table:
# "a coverage table reporting agents, owners, identified operating wallets, metadata, services, reputation coverage, and ownership changes by chain."
coverage_records = []
for chain_name in ["ethereum", "base"]:
    df_c = df_all_agents[df_all_agents["chain"] == chain_name]
    total_agents = len(df_c)
    unique_owners = df_c["owner_wallet"].nunique()
    identified_op_wallets = df_c["operating_wallet"].dropna().nunique()
    agents_with_metadata = (df_c["description"] != "").sum()
    agents_with_services = (df_c["service_count"] > 0).sum()
    agents_with_reputation = (df_c["reputation_feedback_count"] > 0).sum()
    transferred_agents = (df_c["transfer_count"] > 0).sum()
    total_ownership_transfers = df_c["transfer_count"].sum()
    
    coverage_records.append({
        "Chain": chain_name.capitalize(),
        "Total_Agents": total_agents,
        "Unique_Owners": unique_owners,
        "Identified_Operating_Wallets": identified_op_wallets,
        "Agents_With_Metadata": agents_with_metadata,
        "Agents_With_Services": agents_with_services,
        "Agents_With_Reputation": agents_with_reputation,
        "Agents_With_Ownership_Changes": transferred_agents,
        "Total_Ownership_Transfer_Events": total_ownership_transfers
    })

df_coverage = pd.DataFrame(coverage_records)
# Add Total row
df_total = pd.DataFrame([{
    "Chain": "Combined (Total)",
    "Total_Agents": df_coverage["Total_Agents"].sum(),
    "Unique_Owners": df_all_agents["owner_wallet"].nunique(),
    "Identified_Operating_Wallets": df_all_agents["operating_wallet"].dropna().nunique(),
    "Agents_With_Metadata": df_coverage["Agents_With_Metadata"].sum(),
    "Agents_With_Services": df_coverage["Agents_With_Services"].sum(),
    "Agents_With_Reputation": df_coverage["Agents_With_Reputation"].sum(),
    "Agents_With_Ownership_Changes": df_coverage["Agents_With_Ownership_Changes"].sum(),
    "Total_Ownership_Transfer_Events": df_coverage["Total_Ownership_Transfer_Events"].sum()
}])
df_coverage = pd.concat([df_coverage, df_total], ignore_index=True)

coverage_table_path = os.path.join(results_dir, "chain_coverage_table.csv")
df_coverage.to_csv(coverage_table_path, index=False)
print("\n=== ERC-8004 Chain Coverage Table ===")
print(df_coverage.to_string(index=False))
print(f"\nSaved coverage table to {coverage_table_path}")
