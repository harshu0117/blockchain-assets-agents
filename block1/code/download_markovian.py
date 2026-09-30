import urllib.request
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
markov_dir = os.path.join(PROJECT_ROOT, "data", "x402", "markovian")
os.makedirs(markov_dir, exist_ok=True)

files = [
    "README.md",
    "findings.md",
    "facilitators.json",
    "components.json",
    "fleets.json",
    "window.json",
    "x402_pull.py",
    "x402_components.py",
    "x402_facilitators.py"
]

base_url = "https://raw.githubusercontent.com/MarkovianProtocol/x402-second-measurement/main/"
headers = {'User-Agent': 'Mozilla/5.0'}

for f in files:
    target = os.path.join(markov_dir, f)
    url = base_url + f
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp, open(target, "wb") as out_f:
            out_f.write(resp.read())
        print(f"Downloaded {f} ({os.path.getsize(target)} bytes)")
    except Exception as e:
        print(f"Error downloading {f}: {e}")

print("Markovian files downloaded successfully!")
