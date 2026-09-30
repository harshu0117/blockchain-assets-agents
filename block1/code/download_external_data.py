import os
import urllib.request
import json
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
events_dir = os.path.join(PROJECT_ROOT, "data", "events")
x402_dir = os.path.join(PROJECT_ROOT, "data", "x402")
os.makedirs(events_dir, exist_ok=True)
os.makedirs(x402_dir, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Download ERC-8004 Multi-chain Parquet files for Ethereum (1) and Base (8453)
chains = ['1', '8453']
files_to_fetch = ['identity.parquet', 'reputation.parquet', 'cursor.json']

for chain in chains:
    chain_dir = os.path.join(events_dir, chain)
    os.makedirs(chain_dir, exist_ok=True)
    for fname in files_to_fetch:
        target = os.path.join(chain_dir, fname)
        if os.path.exists(target) and os.path.getsize(target) > 0:
            print(f"Already downloaded: {chain}/{fname} ({os.path.getsize(target)} bytes)")
            continue
        url = f"https://huggingface.co/datasets/qntx/erc8004-events/resolve/main/{chain}/{fname}"
        print(f"Downloading {url} -> {target}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp, open(target, "wb") as out_f:
                out_f.write(resp.read())
            print(f"Saved {chain}/{fname} ({os.path.getsize(target)} bytes)")
        except Exception as e:
            print(f"Error downloading {chain}/{fname}: {e}")

# 2. Download x402 datasets
x402_files = [
    ("https://x402stats.io/api/stats/csv", "x402_daily_stats.csv"),
    ("https://x402stats.io/api/stats", "x402_stats_full.json"),
    ("https://x402stats.io/api/facilitators", "x402_facilitators.json"),
    ("https://x402stats.io/llms-full.txt", "x402_llms_full.txt")
]

for url, fname in x402_files:
    target = os.path.join(x402_dir, fname)
    if os.path.exists(target) and os.path.getsize(target) > 0:
        print(f"Already downloaded: {fname} ({os.path.getsize(target)} bytes)")
        continue
    print(f"Downloading {url} -> {target}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp, open(target, "wb") as out_f:
            out_f.write(resp.read())
        print(f"Saved {fname} ({os.path.getsize(target)} bytes)")
    except Exception as e:
        print(f"Error downloading {fname}: {e}")

print("\nData download routine complete!")
