"""
Feedback Decoder for ERC-8004 Reputation Registry
Decodes NewFeedback, FeedbackRevoked, and ResponseAppended events across Ethereum and Base.
"""

import os
import datetime
import pandas as pd
import pyarrow.parquet as pq
from eth_abi import decode
from web3 import Web3
from typing import Tuple, Dict, Any, List

from src.erc8004.constants import (
    CHAINS,
    TOPIC_NEW_FEEDBACK,
    TOPIC_FEEDBACK_REVOKED,
    TOPIC_RESPONSE_APPENDED
)
from src.erc8004.pipeline import block_to_timestamp, format_iso_timestamp

NEW_FEEDBACK_TYPES = ['uint64', 'int128', 'uint8', 'string', 'string', 'string', 'string', 'bytes32']
RESPONSE_TYPES = ['uint64', 'string', 'bytes32']


def decode_chain_reputation(chain_id: int) -> Tuple[pd.DataFrame, Dict[Tuple[int, str, int], Dict[str, Any]], Dict[Tuple[int, str, int], int]]:
    chain_name = CHAINS[chain_id]["name"]
    raw_path = f"data/raw/qntx/{chain_id}/reputation.parquet"
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Missing raw reputation parquet: {raw_path}")

    print(f"Loading {chain_name} (Chain {chain_id}) raw reputation logs...")
    df = pq.read_table(raw_path).to_pandas()
    df = df.sort_values(by=["block_number", "tx_index", "log_index"]).reset_index(drop=True)

    # 1. Parse FeedbackRevoked events
    # FeedbackRevoked(uint256 indexed agentId, address indexed clientAddress, uint64 indexed feedbackIndex)
    revocations = {}
    revoked_mask = df["topic0"].str.lower() == TOPIC_FEEDBACK_REVOKED.lower()
    df_rev = df[revoked_mask]
    print(f"Parsing {len(df_rev)} revocation events for {chain_name}...")
    for _, r in df_rev.iterrows():
        try:
            aid = int(r["topic1"], 16)
            client = Web3.to_checksum_address("0x" + r["topic2"][-40:])
            fb_idx = int(r["topic3"], 16)
            revocations[(aid, client.lower(), fb_idx)] = {
                "revoked_block": int(r["block_number"]),
                "revoked_tx_hash": r["tx_hash"]
            }
        except Exception:
            continue

    # 2. Parse ResponseAppended events
    # ResponseAppended(uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex, address indexed responder, ...)
    responses = {}
    resp_mask = df["topic0"].str.lower() == TOPIC_RESPONSE_APPENDED.lower()
    df_resp = df[resp_mask]
    print(f"Parsing {len(df_resp)} response appended events for {chain_name}...")
    for _, r in df_resp.iterrows():
        try:
            aid = int(r["topic1"], 16)
            client = Web3.to_checksum_address("0x" + r["topic2"][-40:])
            raw = bytes.fromhex(r["data"][2:] if r["data"].startswith("0x") else r["data"])
            fb_idx, _, _ = decode(RESPONSE_TYPES, raw)
            key = (aid, client.lower(), int(fb_idx))
            responses[key] = responses.get(key, 0) + 1
        except Exception:
            continue

    # 3. Parse NewFeedback events
    new_fb_mask = df["topic0"].str.lower() == TOPIC_NEW_FEEDBACK.lower()
    df_new = df[new_fb_mask]
    print(f"Decoding {len(df_new)} NewFeedback events for {chain_name}...")

    feedback_records = []
    for _, r in df_new.iterrows():
        try:
            aid = int(r["topic1"], 16)
            client = Web3.to_checksum_address("0x" + r["topic2"][-40:])
            blk = int(r["block_number"])
            tx_h = r["tx_hash"]
            tx_i = int(r["tx_index"])
            log_i = int(r["log_index"])
            ts = block_to_timestamp(chain_id, blk)
            ts_iso = format_iso_timestamp(ts)
            dt_str = ts_iso[:10]

            raw = bytes.fromhex(r["data"][2:] if r["data"].startswith("0x") else r["data"])
            fb_idx, val, dec, tag1, tag2, endpoint, uri, fb_hash = decode(NEW_FEEDBACK_TYPES, raw)

            fb_idx = int(fb_idx)
            val = int(val)
            dec = int(dec)
            norm_val = float(val / (10 ** dec)) if dec > 0 else float(val)

            rev_info = revocations.get((aid, client.lower(), fb_idx))
            is_rev = rev_info is not None
            resp_cnt = responses.get((aid, client.lower(), fb_idx), 0)

            feedback_records.append({
                "chain": chain_name,
                "chain_id": chain_id,
                "agent_id": aid,
                "provider_wallet": client,
                "feedback_index": fb_idx,
                "block_number": blk,
                "tx_hash": tx_h,
                "tx_index": tx_i,
                "log_index": log_i,
                "timestamp": ts_iso,
                "timestamp_unix": ts,
                "date": dt_str,
                "raw_value": str(val),
                "value_decimals": dec,
                "normalized_value": norm_val,
                "tag1": tag1.strip() if tag1 else "",
                "tag2": tag2.strip() if tag2 else "",
                "endpoint": endpoint.strip() if endpoint else "",
                "feedback_uri": uri.strip() if uri else "",
                "feedback_hash": "0x" + fb_hash.hex() if isinstance(fb_hash, bytes) else str(fb_hash),
                "is_revoked": is_rev,
                "revocation_block": rev_info["revoked_block"] if is_rev else None,
                "revocation_tx_hash": rev_info["revoked_tx_hash"] if is_rev else None,
                "has_response": resp_cnt > 0,
                "response_count": resp_cnt
            })
        except Exception:
            continue

    df_feedback = pd.DataFrame(feedback_records)
    print(f"Decoded {len(df_feedback)} clean feedback records for {chain_name}.")
    return df_feedback, revocations, responses
