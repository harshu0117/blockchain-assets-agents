import urllib.request
import json

topics = [
    '0x2c149ed548c6d2993cd73efe187df6eccabe4538091b33adbd25fafdb8a1468b',
    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
    '0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a',
    '0xf8e1a15aba9398e019f0b49df1a4fde98ee17ae345cb5f6b5e2c27f5033e8ce7',
    '0x3a2c7fffc2cba7582c690e3b82c453ea02a308326a98a3ad7576c606336409fb',
    '0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc',
    '0xb1c6be0b5b8aef6539e2fac0fd131a2faa7b49edf8e505b5eb0ad487d56051d4',
    '0x25156fd3288212246d8b008d5921fde376c71ed14ac2e072a506eb06fde6d09d'
]

url = "https://api.openchain.xyz/signature-database/v1/lookup?event=" + ",".join(topics)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        event_map = res.get('result', {}).get('event', {})
        for t in topics:
            names = [item['name'] for item in event_map.get(t, [])]
            print(f"{t[:10]}... -> {names}")
except Exception as e:
    print("Openchain error:", e)
