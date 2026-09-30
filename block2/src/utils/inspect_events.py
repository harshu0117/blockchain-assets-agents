import json
from web3 import Web3
import pyarrow.parquet as pq

with open('references/erc-8004-contracts/abis/IdentityRegistry.json') as f:
    abi = json.load(f)

w3 = Web3()
event_topics = {}
for item in abi:
    if item.get('type') == 'event':
        name = item['name']
        inputs = [inp['type'] for inp in item.get('inputs', [])]
        sig = f"{name}({','.join(inputs)})"
        topic0 = '0x' + w3.keccak(text=sig).hex()
        event_topics[topic0.lower()] = (name, sig)

print("Known ABI Event Topics:")
for t, (name, sig) in event_topics.items():
    print(f"{t}: {sig}")

for chain_id in ['1', '8453']:
    t_id = pq.read_table(f'data/raw/qntx/{chain_id}/identity.parquet')
    df = t_id.to_pandas()
    counts = df['topic0'].str.lower().value_counts()
    print(f"\n--- Chain {chain_id} distinct topic0 counts (Total: {len(df)}) ---")
    for top, count in counts.items():
        name_sig = event_topics.get(top, ("UNKNOWN", "UNKNOWN"))
        print(f"  {top} [{name_sig[0]}]: {count}")
