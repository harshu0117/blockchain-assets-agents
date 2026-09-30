import urllib.request
import json

base_rpc = "https://mainnet.base.org"

payload = {
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
}

req = urllib.request.Request(
    base_rpc,
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        block_hex = result.get('result')
        block_int = int(block_hex, 16)
        print(f"Current Base Block Number: {block_int} ({block_hex})")
except Exception as e:
    print(f"Error querying Base RPC: {e}")
