import pandas as pd
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")

for chain in ['1', '8453']:
    id_path = os.path.join(events_dir, chain, "identity.parquet")
    rep_path = os.path.join(events_dir, chain, "reputation.parquet")
    
    df_id = pd.read_parquet(id_path)
    print(f"=== Chain {chain} Identity Events ===")
    print("Shape:", df_id.shape)
    print("Columns:", list(df_id.columns))
    print(df_id.head(3))
    if 'event_name' in df_id.columns:
        print("Event names:", df_id['event_name'].value_counts())
    
    df_rep = pd.read_parquet(rep_path)
    print(f"\n=== Chain {chain} Reputation Events ===")
    print("Shape:", df_rep.shape)
    print("Columns:", list(df_rep.columns))
    print(df_rep.head(3))
    if 'event_name' in df_rep.columns:
        print("Event names:", df_rep['event_name'].value_counts())
    print("\n" + "="*50 + "\n")
