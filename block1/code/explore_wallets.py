import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(PROJECT_ROOT, "data", "erc8004")

extracted = []
with open(os.path.join(data_dir, "metadata_raw_snapshot.jsonl"), "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        aid = item.get("agent_id")
        raw_text = item.get("raw_text", "")
        if not raw_text:
            continue
        try:
            parsed = json.loads(raw_text)
            wallets = parsed.get("wallets")
            if wallets:
                extracted.append((aid, parsed.get("name"), wallets))
        except Exception:
            pass

print(f"Total agents with structured 'wallets' object in metadata: {len(extracted)}")
for aid, name, w in extracted:
    print(f"Agent {aid} ({name}): {w}")
