import pandas as pd
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")

for chain in ['1', '8453']:
    print(f"=== Chain {chain} ===")
    df_id = pd.read_parquet(os.path.join(events_dir, chain, "identity.parquet"))
    print("Identity unique topic0 counts:")
    print(df_id['topic0'].value_counts())
    
    df_rep = pd.read_parquet(os.path.join(events_dir, chain, "reputation.parquet"))
    print("\nReputation unique topic0 counts:")
    print(df_rep['topic0'].value_counts())
    print("\n" + "="*50)
