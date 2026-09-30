import pandas as pd
import numpy as np
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(PROJECT_ROOT, "data", "erc8004")

print("--- 1. AGENTS CORE ---")
df_agents = pd.read_csv(os.path.join(data_dir, "agents_core.tab"), sep="\t")
print(f"Total Agents: {len(df_agents)}")
print("Columns:", list(df_agents.columns))
print(f"Unique Owners: {df_agents['owner_wallet'].nunique()}")
print(f"Non-null Agent Wallets: {df_agents['agent_wallet'].dropna().count()}")
print(f"Unique Agent Wallets: {df_agents['agent_wallet'].dropna().nunique()}")
print("Lifecycle Status Breakdown:\n", df_agents['lifecycle_status'].value_counts())
print("Metadata Hosting Breakdown:\n", df_agents['metadata_hosting_type'].value_counts().head(5))

print("\n--- 2. AGENT METADATA & X402 SUPPORT ---")
df_meta = pd.read_csv(os.path.join(data_dir, "agent_metadata.tab"), sep="\t")
print(f"Total Metadata Records: {len(df_meta)}")
print("Columns:", list(df_meta.columns))
print("x402 Support Counts:\n", df_meta['x402_support'].value_counts(dropna=False))
print(f"Active Agents in Metadata: {df_meta['active'].value_counts(dropna=False)}")

print("\n--- 3. AGENT SERVICES ---")
df_services = pd.read_csv(os.path.join(data_dir, "agent_services.tab"), sep="\t")
print(f"Total Service Declarations: {len(df_services)}")
print("Columns:", list(df_services.columns))
print("Service Name Distribution:\n", df_services['service_name'].value_counts())

print("\n--- 4. MINT ECONOMICS (STRIKE PRICE / CAPITAL COST) ---")
df_mint = pd.read_csv(os.path.join(data_dir, "mint_economics.tab"), sep="\t")
print(f"Total Mint Tx: {len(df_mint)}")
print("Columns:", list(df_mint.columns))
print("Gas Used Summary:\n", df_mint['gas_used'].describe())
print("Mint Cost ETH Summary:\n", df_mint['mint_cost_eth'].describe())

print("\n--- 5. REPUTATION SUMMARY ---")
df_rep = pd.read_csv(os.path.join(data_dir, "agent_reputation_summary.tab"), sep="\t")
print(f"Total Agents with Reputation Records: {len(df_rep)}")
print("Columns:", list(df_rep.columns))
print(f"Agents with feedback > 0: {(df_rep['feedback_count_total'] > 0).sum()}")
if (df_rep['feedback_count_total'] > 0).sum() > 0:
    print(df_rep[df_rep['feedback_count_total'] > 0].describe())

print("\n--- 6. TRANSFER HISTORY ---")
df_transfers = pd.read_csv(os.path.join(data_dir, "transfer_history.tab"), sep="\t")
print(f"Total Transfers: {len(df_transfers)}")
print("Columns:", list(df_transfers.columns))
print(f"Unique from_wallets: {df_transfers['from_wallet'].nunique()}, to_wallets: {df_transfers['to_wallet'].nunique()}")
