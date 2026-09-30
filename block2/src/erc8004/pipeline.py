"""
End-to-End ERC-8004 Extraction and Ingestion Pipeline
Processes Ethereum and Base multi-chain archives to construct:
- erc8004_events
- erc8004_agents
- Coverage Table
"""

import os
import json
import datetime
import pandas as pd
import pyarrow.parquet as pq
from eth_abi import decode
from web3 import Web3

from src.erc8004.constants import (
    CHAINS,
    TOPIC_REGISTERED,
    TOPIC_TRANSFER,
    TOPIC_URI_UPDATED,
    TOPIC_METADATA_SET,
    TOPIC_NEW_FEEDBACK,
    TOPIC_FEEDBACK_REVOKED,
    ZERO_ADDRESS
)
from src.erc8004.metadata_parser import MetadataResolver


def block_to_timestamp(chain_id: int, block_number: int) -> int:
    """Estimates block timestamp based on chain block time and known anchor."""
    cfg = CHAINS[chain_id]
    delta_blocks = block_number - cfg["anchor_block"]
    delta_seconds = int(delta_blocks * cfg["block_time_seconds"])
    return cfg["anchor_timestamp"] + delta_seconds


def format_iso_timestamp(ts: int) -> str:
    """Formats unix timestamp into ISO 8601 UTC string."""
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def process_chain_events(chain_id: int):
    chain_name = CHAINS[chain_id]["name"]
    raw_path = f"data/raw/qntx/{chain_id}/identity.parquet"
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Missing raw identity parquet for chain {chain_id}: {raw_path}")

    print(f"Loading {chain_name} (Chain {chain_id}) raw events...")
    df = pq.read_table(raw_path).to_pandas()
    # Sort strictly in chronological execution order
    df = df.sort_values(by=["block_number", "tx_index", "log_index"]).reset_index(drop=True)

    extracted_events = []
    
    # Trackers for agents state
    agents_state = {}

    print(f"Decoding {len(df)} logs for {chain_name}...")
    for idx, row in df.iterrows():
        t0 = row["topic0"].lower() if row["topic0"] else ""
        blk = int(row["block_number"])
        tx_hash = row["tx_hash"]
        tx_idx = int(row["tx_index"])
        log_idx = int(row["log_index"])
        ts = block_to_timestamp(chain_id, blk)
        ts_iso = format_iso_timestamp(ts)
        data_str = row["data"]
        raw_bytes = bytes.fromhex(data_str[2:] if data_str.startswith("0x") else data_str)

        # 1. Registered Event
        if t0 == TOPIC_REGISTERED.lower():
            try:
                agent_id = int(row["topic1"], 16)
                owner = Web3.to_checksum_address("0x" + row["topic2"][-40:])
                uri = decode(["string"], raw_bytes)[0]
            except Exception:
                continue

            extracted_events.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": agent_id,
                "event_type": "Registered",
                "block_number": blk,
                "timestamp": ts_iso,
                "timestamp_unix": ts,
                "tx_hash": tx_hash,
                "tx_index": tx_idx,
                "log_index": log_idx,
                "from_address": None,
                "to_address": owner,
                "operating_wallet": None,
                "uri": uri,
                "metadata_key": None,
                "metadata_value": None
            })

            if agent_id not in agents_state:
                agents_state[agent_id] = {
                    "agent_id": agent_id,
                    "chain": chain_name,
                    "chain_id": chain_id,
                    "registration_block": blk,
                    "registration_timestamp": ts_iso,
                    "registration_tx_hash": tx_hash,
                    "initial_owner_wallet": owner,
                    "current_owner_wallet": owner,
                    "owner_changes_count": 0,
                    "operating_wallet": None,
                    "operating_wallet_source": "NONE",
                    "operating_wallet_confidence": "NONE",
                    "latest_uri": uri,
                }
            else:
                agents_state[agent_id]["initial_owner_wallet"] = owner
                agents_state[agent_id]["current_owner_wallet"] = owner
                if not agents_state[agent_id]["latest_uri"]:
                    agents_state[agent_id]["latest_uri"] = uri

        # 2. Transfer Event (Mints & Ownership Transfers)
        elif t0 == TOPIC_TRANSFER.lower():
            try:
                from_addr = Web3.to_checksum_address("0x" + row["topic1"][-40:])
                to_addr = Web3.to_checksum_address("0x" + row["topic2"][-40:])
                agent_id = int(row["topic3"], 16)
            except Exception:
                continue

            is_mint = (from_addr.lower() == ZERO_ADDRESS.lower())
            ev_type = "MintTransfer" if is_mint else "OwnershipTransferred"

            extracted_events.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": agent_id,
                "event_type": ev_type,
                "block_number": blk,
                "timestamp": ts_iso,
                "timestamp_unix": ts,
                "tx_hash": tx_hash,
                "tx_index": tx_idx,
                "log_index": log_idx,
                "from_address": from_addr,
                "to_address": to_addr,
                "operating_wallet": None,
                "uri": None,
                "metadata_key": None,
                "metadata_value": None
            })

            if agent_id not in agents_state:
                agents_state[agent_id] = {
                    "agent_id": agent_id,
                    "chain": chain_name,
                    "chain_id": chain_id,
                    "registration_block": blk,
                    "registration_timestamp": ts_iso,
                    "registration_tx_hash": tx_hash,
                    "initial_owner_wallet": to_addr,
                    "current_owner_wallet": to_addr,
                    "owner_changes_count": 0,
                    "operating_wallet": None,
                    "operating_wallet_source": "NONE",
                    "operating_wallet_confidence": "NONE",
                    "latest_uri": None,
                }
            else:
                if not is_mint:
                    # Token transfer clears operating wallet in contract
                    agents_state[agent_id]["current_owner_wallet"] = to_addr
                    agents_state[agent_id]["owner_changes_count"] += 1
                    agents_state[agent_id]["operating_wallet"] = None
                    agents_state[agent_id]["operating_wallet_source"] = "CLEARED_BY_TRANSFER"
                    agents_state[agent_id]["operating_wallet_confidence"] = "NONE"

        # 3. URIUpdated Event
        elif t0 == TOPIC_URI_UPDATED.lower():
            try:
                agent_id = int(row["topic1"], 16)
                updated_by = Web3.to_checksum_address("0x" + row["topic2"][-40:])
                new_uri = decode(["string"], raw_bytes)[0]
            except Exception:
                continue

            extracted_events.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": agent_id,
                "event_type": "URIUpdated",
                "block_number": blk,
                "timestamp": ts_iso,
                "timestamp_unix": ts,
                "tx_hash": tx_hash,
                "tx_index": tx_idx,
                "log_index": log_idx,
                "from_address": None,
                "to_address": updated_by,
                "operating_wallet": None,
                "uri": new_uri,
                "metadata_key": None,
                "metadata_value": None
            })

            if agent_id in agents_state:
                agents_state[agent_id]["latest_uri"] = new_uri

        # 4. MetadataSet Event (including setAgentWallet & unsetAgentWallet)
        elif t0 == TOPIC_METADATA_SET.lower():
            try:
                agent_id = int(row["topic1"], 16)
                meta_key, meta_val = decode(["string", "bytes"], raw_bytes)
            except Exception:
                continue

            wallet_addr = None
            ev_type = "MetadataSet"
            if meta_key == "agentWallet":
                if len(meta_val) == 20:
                    wallet_addr = Web3.to_checksum_address("0x" + meta_val.hex())
                    ev_type = "WalletUpdated"
                else:
                    wallet_addr = None
                    ev_type = "WalletCleared"

            extracted_events.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": agent_id,
                "event_type": ev_type,
                "block_number": blk,
                "timestamp": ts_iso,
                "timestamp_unix": ts,
                "tx_hash": tx_hash,
                "tx_index": tx_idx,
                "log_index": log_idx,
                "from_address": None,
                "to_address": None,
                "operating_wallet": wallet_addr,
                "uri": None,
                "metadata_key": meta_key,
                "metadata_value": meta_val.hex() if meta_val else ""
            })

            if agent_id in agents_state:
                if meta_key == "agentWallet":
                    if wallet_addr:
                        agents_state[agent_id]["operating_wallet"] = wallet_addr
                        agents_state[agent_id]["operating_wallet_source"] = "ONCHAIN_REGISTRY_EVENT"
                        agents_state[agent_id]["operating_wallet_confidence"] = "HIGH"
                    else:
                        agents_state[agent_id]["operating_wallet"] = None
                        agents_state[agent_id]["operating_wallet_source"] = "UNSET_EVENT"
                        agents_state[agent_id]["operating_wallet_confidence"] = "NONE"

    print(f"Decoded {len(extracted_events)} relevant lifecycle events across {len(agents_state)} agents on {chain_name}.")
    return extracted_events, agents_state


def get_reputation_stats(chain_id: int):
    """Computes feedback counts per agent from reputation.parquet."""
    rep_path = f"data/raw/qntx/{chain_id}/reputation.parquet"
    if not os.path.exists(rep_path):
        return {}
    df_rep = pq.read_table(rep_path).to_pandas()
    # Filter for NewFeedback events
    new_fb = df_rep[df_rep["topic0"].str.lower() == TOPIC_NEW_FEEDBACK.lower()]
    feedback_counts = {}
    for t1 in new_fb["topic1"]:
        try:
            aid = int(t1, 16)
            feedback_counts[aid] = feedback_counts.get(aid, 0) + 1
        except Exception:
            pass
    return feedback_counts


def run_pipeline():
    print("=" * 60)
    print("Starting Phase 1 ERC-8004 Extraction & Ingestion Pipeline")
    print("=" * 60)

    resolver = MetadataResolver(dataverse_dir="data/raw/dataverse")
    all_events = []
    all_agents = []

    for chain_id in [1, 8453]:
        events, agents_dict = process_chain_events(chain_id)
        all_events.extend(events)

        feedback_counts = get_reputation_stats(chain_id)
        print(f"Chain {chain_id}: {len(feedback_counts)} agents have recorded feedback in reputation registry.")

        for agent_id, state in sorted(agents_dict.items()):
            # Resolve off-chain metadata & services
            meta = resolver.resolve_agent_metadata(chain_id, agent_id, state["latest_uri"])

            # If operating wallet wasn't set on-chain, check if declared in metadata
            if not state["operating_wallet"] and meta.get("declared_wallet"):
                state["operating_wallet"] = Web3.to_checksum_address(meta["declared_wallet"])
                state["operating_wallet_source"] = "OFFCHAIN_METADATA_DECLARED"
                state["operating_wallet_confidence"] = "MEDIUM"

            fb_count = feedback_counts.get(agent_id, 0)
            has_rep = (fb_count > 0)

            all_agents.append({
                "agent_id": agent_id,
                "chain": state["chain"],
                "chain_id": state["chain_id"],
                "registration_block": state["registration_block"],
                "registration_timestamp": state["registration_timestamp"],
                "registration_tx_hash": state["registration_tx_hash"],
                "initial_owner_wallet": state["initial_owner_wallet"],
                "current_owner_wallet": state["current_owner_wallet"],
                "owner_changes_count": state["owner_changes_count"],
                "operating_wallet": state["operating_wallet"],
                "operating_wallet_source": state["operating_wallet_source"],
                "operating_wallet_confidence": state["operating_wallet_confidence"],
                "token_uri": state["latest_uri"],
                "name": meta["name"],
                "description": meta["description"],
                "x402_support": meta["x402_support"],
                "active": meta["active"],
                "declared_services": json.dumps(meta["declared_services"]),
                "service_count": meta["service_count"],
                "has_reputation": has_rep,
                "reputation_feedback_count": fb_count
            })

    # Convert to DataFrames
    df_events = pd.DataFrame(all_events)
    df_agents = pd.DataFrame(all_agents)

    # Save processed event logs
    os.makedirs("data/processed", exist_ok=True)
    events_pq_path = "data/processed/erc8004_events.parquet"
    events_csv_path = "data/processed/erc8004_events.csv"
    df_events.to_parquet(events_pq_path, index=False)
    # Save a sample CSV for easy inspection
    df_events.head(10000).to_csv(events_csv_path, index=False)
    print(f"Saved {len(df_events)} events to {events_pq_path} and preview to {events_csv_path}")

    # Save processed agent table
    agents_pq_path = "data/processed/erc8004_agents.parquet"
    agents_csv_path = "data/processed/erc8004_agents.csv"
    df_agents.to_parquet(agents_pq_path, index=False)
    df_agents.to_csv(agents_csv_path, index=False)
    print(f"Saved {len(df_agents)} agents to {agents_pq_path} and {agents_csv_path}")

    # Construct Phase 1 Coverage Table
    os.makedirs("results/tables", exist_ok=True)
    coverage_rows = []
    for chain_name in ["ethereum", "base", "total"]:
        if chain_name == "total":
            sub_agents = df_agents
            sub_events = df_events
        else:
            sub_agents = df_agents[df_agents["chain"] == chain_name]
            sub_events = df_events[df_events["chain"] == chain_name]

        total_agents = len(sub_agents)
        unique_owners = sub_agents["current_owner_wallet"].nunique()
        identified_operating = sub_agents["operating_wallet"].notna().sum()
        high_conf_operating = (sub_agents["operating_wallet_confidence"] == "HIGH").sum()
        med_conf_operating = (sub_agents["operating_wallet_confidence"] == "MEDIUM").sum()
        with_metadata = sub_agents["token_uri"].apply(lambda u: bool(u and str(u).strip() != "")).sum()
        with_services = (sub_agents["service_count"] > 0).sum()
        with_reputation = sub_agents["has_reputation"].sum()
        ownership_changes = (sub_agents["owner_changes_count"] > 0).sum()
        total_transfers = (sub_events["event_type"] == "OwnershipTransferred").sum()

        coverage_rows.append({
            "Chain": chain_name.capitalize(),
            "Total Agents": total_agents,
            "Unique Current Owners": unique_owners,
            "Operating Wallets Identified": identified_operating,
            "Operating Wallets (High Conf - On-Chain)": high_conf_operating,
            "Operating Wallets (Med Conf - Declared)": med_conf_operating,
            "Operating Wallet Coverage (%)": round(100.0 * identified_operating / total_agents, 2) if total_agents else 0.0,
            "Agents with Metadata": with_metadata,
            "Metadata Coverage (%)": round(100.0 * with_metadata / total_agents, 2) if total_agents else 0.0,
            "Agents with Services": with_services,
            "Services Coverage (%)": round(100.0 * with_services / total_agents, 2) if total_agents else 0.0,
            "Agents with Reputation": with_reputation,
            "Reputation Coverage (%)": round(100.0 * with_reputation / total_agents, 2) if total_agents else 0.0,
            "Agents with Ownership Changes": ownership_changes,
            "Total Ownership Transfer Events": total_transfers
        })

    df_cov = pd.DataFrame(coverage_rows)
    cov_csv_path = "results/tables/coverage_table_phase1.csv"
    cov_md_path = "results/tables/coverage_table_phase1.md"
    df_cov.to_csv(cov_csv_path, index=False)
    with open(cov_md_path, "w", encoding="utf-8") as f:
        f.write("# ERC-8004 Coverage Table (Phase 1)\n\n")
        f.write(df_cov.to_markdown(index=False))
        f.write("\n")

    print("\nPhase 1 Coverage Table Generated:")
    print(df_cov.to_string())
    print("\nPhase 1 Pipeline execution completed successfully!")


if __name__ == "__main__":
    run_pipeline()
