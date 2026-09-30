import pandas as pd
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

for chain in ['1', '8453']:
    df = pd.read_parquet(os.path.join(events_dir, chain, "identity.parquet"))
    df_tr = df[df['topic0'] == TRANSFER_TOPIC]
    sample = df_tr.head(3)
    print(f"=== Chain {chain} Transfer sample ===")
    for idx, r in sample.iterrows():
        from_w = '0x' + str(r['topic1'])[-40:]
        to_w = '0x' + str(r['topic2'])[-40:]
        token_id = int(str(r['topic3']), 16) if r['topic3'] else None
        print(f"Block {r['block_number']}: from {from_w} to {to_w}, tokenId={token_id}, tx={r['tx_hash'][:16]}...")
