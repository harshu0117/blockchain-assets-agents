import urllib.request
import json
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
data_dir = os.path.join(PROJECT_ROOT, "data", "erc8004")
os.makedirs(data_dir, exist_ok=True)

manifest_path = os.path.join(PROJECT_ROOT, "data", "dataverse_files.json")
with open(manifest_path, "r") as f:
    files = json.load(f)

print(f"Downloading {len(files)} files to {data_dir}...")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for idx, file_info in enumerate(files, 1):
    fname = file_info["filename"]
    fid = file_info["id"]
    # Dataverse download endpoint
    download_url = f"https://dataverse.harvard.edu/api/access/datafile/{fid}"
    target_path = os.path.join(data_dir, fname)
    
    print(f"[{idx}/{len(files)}] Downloading {fname} from {download_url}...")
    req = urllib.request.Request(download_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp, open(target_path, "wb") as out_f:
            out_f.write(resp.read())
        size = os.path.getsize(target_path)
        print(f" -> Saved {fname} ({size} bytes)")
    except Exception as e:
        print(f" -> Failed to download {fname}: {e}")
    time.sleep(0.5)

print("\nAll downloads finished successfully!")
