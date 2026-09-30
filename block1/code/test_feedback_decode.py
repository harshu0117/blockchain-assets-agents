import pandas as pd
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")

NEW_FEEDBACK = "0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc"

for chain in ['1', '8453']:
    df = pd.read_parquet(os.path.join(events_dir, chain, "reputation.parquet"))
    df_fb = df[df['topic0'] == NEW_FEEDBACK]
    print(f"=== Chain {chain} Feedback count: {len(df_fb)} ===")
    sample = df_fb.head(3)
    for idx, r in sample.iterrows():
        aid = int(str(r['topic1']), 16) if r['topic1'] else None
        client = '0x' + str(r['topic2'])[-40:] if r['topic2'] else None
        fb_idx = int(str(r['topic3']), 16) if r['topic3'] else None
        print(f"Block {r['block_number']}: agentId={aid}, client={client}, fb_idx={fb_idx}, data_len={len(str(r['data']))}")
