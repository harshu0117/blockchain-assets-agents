import pandas as pd
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")

REGISTERED_TOPIC = "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

for chain in ['1', '8453']:
    df = pd.read_parquet(os.path.join(events_dir, chain, "identity.parquet"))
    df_reg = df[df['topic0'] == REGISTERED_TOPIC]
    df_tr = df[df['topic0'] == TRANSFER_TOPIC]
    print(f"Chain {chain}: Total rows={len(df)}, Registered events={len(df_reg)}, Transfers={len(df_tr)}")
    
    # Check sample Registered event
    if len(df_reg) > 0:
        row = df_reg.iloc[0]
        # In Registered(uint256 indexed agentId, string tokenURI, address indexed owner)
        # topic1 = agentId, topic2 = owner, or data contains URI
        print(f"Sample Reg Chain {chain}: topic1={row['topic1']}, topic2={row['topic2']}, topic3={row['topic3']}")
        if row['topic1']:
            try:
                aid = int(row['topic1'], 16)
                print(f"Decoded agentId from topic1: {aid}")
            except Exception as e:
                print("Decode error:", e)
        if row['topic2']:
            try:
                owner = '0x' + row['topic2'][-40:]
                print(f"Decoded owner from topic2: {owner}")
            except Exception as e:
                pass
