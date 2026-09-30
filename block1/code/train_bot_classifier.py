import os
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score, confusion_matrix

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
output_dir = os.path.join(PROJECT_ROOT, "results")
os.makedirs(output_dir, exist_ok=True)

csv_path = os.path.join(PROJECT_ROOT, "data", "benchmark", "transaction_dataset.csv")
print(f"Loading dataset from {csv_path}...")
df = pd.read_csv(csv_path)

# 1. Cleaning & Preprocessing
# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Drop identifiers / non-numeric columns
cols_to_drop = ['Unnamed: 0', 'Index', 'Address', 'ERC20 most sent token type', 'ERC20_most_rec_token_type']
cols_to_drop = [c for c in cols_to_drop if c in df.columns]
df_clean = df.drop(columns=cols_to_drop)

# Separate features and target
X = df_clean.drop(columns=['FLAG'])
y = df_clean['FLAG']

# Impute missing values with median
X = X.apply(pd.to_numeric, errors='coerce')
X = X.fillna(X.median())

# Remove any zero-variance columns
var_threshold = 1e-6
valid_cols = X.columns[X.var() > var_threshold]
X = X[valid_cols]

print(f"Preprocessed features shape: {X.shape}")
print(f"Class distribution: {y.value_counts().to_dict()} (Imbalance: {y.mean():.4f})")

# 2. Train-Test Split (Stratified 80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# 3. Model Training: Random Forest
rf = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, class_weight='balanced')
rf.fit(X_train, y_train)

# Predictions & Probabilities
y_pred_rf = rf.predict(X_test)
y_prob_rf = rf.predict_proba(X_test)[:, 1]

roc_rf = roc_auc_score(y_test, y_prob_rf)
pr_auc_rf = average_precision_score(y_test, y_prob_rf)
cm_rf = confusion_matrix(y_test, y_pred_rf)

print("\n--- RANDOM FOREST CLASSIFIER RESULTS ---")
print(f"ROC-AUC Score: {roc_rf:.4f}")
print(f"PR-AUC (Average Precision): {pr_auc_rf:.4f}")
print("Confusion Matrix:\n", cm_rf)
print("\nClassification Report:\n", classification_report(y_test, y_pred_rf))

# 4. Feature Importance Analysis
feature_importances = pd.DataFrame({
    'Feature': X.columns,
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nTop 15 Most Discriminative Features:")
print(feature_importances.head(15).to_string(index=False))

# Save Feature Importances
feature_importances.to_csv(os.path.join(output_dir, "feature_importances.csv"), index=False)

# 5. Model Training: Gradient Boosting (Benchmark)
gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
gb.fit(X_train, y_train)
y_prob_gb = gb.predict_proba(X_test)[:, 1]
roc_gb = roc_auc_score(y_test, y_prob_gb)
pr_auc_gb = average_precision_score(y_test, y_prob_gb)

print("\n--- GRADIENT BOOSTING CLASSIFIER RESULTS ---")
print(f"ROC-AUC Score: {roc_gb:.4f}")
print(f"PR-AUC: {pr_auc_gb:.4f}")

# 6. Save Metrics Summary
metrics = {
    "random_forest": {
        "roc_auc": float(roc_rf),
        "pr_auc": float(pr_auc_rf),
        "confusion_matrix": cm_rf.tolist(),
        "n_features": int(X.shape[1]),
        "test_size": len(y_test)
    },
    "gradient_boosting": {
        "roc_auc": float(roc_gb),
        "pr_auc": float(pr_auc_gb)
    },
    "top_features": feature_importances.head(10).to_dict(orient="records")
}

with open(os.path.join(output_dir, "model_metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

# 7. Generate Feature Importance Plot
plt.figure(figsize=(10, 6))
top_12 = feature_importances.head(12)
plt.barh(top_12['Feature'][::-1], top_12['Importance'][::-1], color='#1f77b4', edgecolor='black')
plt.xlabel("Gini Feature Importance")
plt.title("Key Behavioral Features: Autonomous / Bot vs. Human Wallets")
plt.tight_layout()
plot_path = os.path.join(output_dir, "feature_importance_plot.png")
plt.savefig(plot_path, dpi=300)
plt.close()

print(f"\nSaved metrics to {output_dir}/model_metrics.json and plot to {plot_path}")
