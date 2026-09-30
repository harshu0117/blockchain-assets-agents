import pandas as pd
import numpy as np
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
csv_path = os.path.join(PROJECT_ROOT, "data", "benchmark", "transaction_dataset.csv")
df = pd.read_csv(csv_path)

print("Dataset Shape:", df.shape)
print("\nClass distribution (FLAG):")
print(df['FLAG'].value_counts(normalize=True))

print("\nColumns:")
for i, c in enumerate(df.columns):
    print(f"{i}: {c.strip()}")

print("\nSample stats for FLAG 0 (Human/Regular) vs FLAG 1 (Automated/Anomalous):")
time_col = 'Avg min between sent tnx'
val_col = 'Avg min between received tnx'
tx_col = 'Sent tnx'

summary = df.groupby('FLAG')[[time_col, val_col, tx_col, 'total Ether sent', 'total ether received']].median()
print(summary)
