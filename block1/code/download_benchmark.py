import urllib.request
import os
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
bench_dir = os.path.join(PROJECT_ROOT, "data", "benchmark")
os.makedirs(bench_dir, exist_ok=True)
csv_path = os.path.join(bench_dir, "transaction_dataset.csv")

url = 'https://raw.githubusercontent.com/pavan178/AI_FOR_BLOCKCHAIN/master/transaction_dataset.csv'
print(f"Downloading benchmark dataset to {csv_path}...")
urllib.request.urlretrieve(url, csv_path)

df = pd.read_csv(csv_path)
print(f"Loaded successfully! Shape: {df.shape}")
print("Target variable counts (FLAG):\n", df['FLAG'].value_counts())
print("\nTop 15 Features:")
for col in list(df.columns)[:15]:
    print(f"- {col}")
