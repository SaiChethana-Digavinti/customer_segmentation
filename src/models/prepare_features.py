import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/rfm_scored_customers.csv"
)

OUTPUT_FILE = Path(
    "data/processed/ml_ready_features.csv"
)


# ---------------------------------------------------------
# 2. Load RFM scored data
# ---------------------------------------------------------

print("Loading RFM scored customer data...")

rfm = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(rfm):,}")


# ---------------------------------------------------------
# 3. Select features for clustering
# ---------------------------------------------------------

features = [
    "Recency",
    "Frequency",
    "Monetary"
]

X = rfm[features].copy()


# ---------------------------------------------------------
# 4. Check for missing values
# ---------------------------------------------------------

print("\nMissing values before transformation:")

print(X.isnull().sum())


# ---------------------------------------------------------
# 5. Log transformation
# ---------------------------------------------------------

# Log transformation reduces the effect of extreme
# values and makes highly skewed features more suitable
# for clustering.

X_log = np.log1p(X)


# ---------------------------------------------------------
# 6. Standardize features
# ---------------------------------------------------------

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X_log)


# ---------------------------------------------------------
# 7. Convert back to DataFrame
# ---------------------------------------------------------

X_scaled = pd.DataFrame(
    X_scaled,
    columns=[
        "Recency_scaled",
        "Frequency_scaled",
        "Monetary_scaled"
    ]
)


# ---------------------------------------------------------
# 8. Combine customer ID + original RFM + scaled features
# ---------------------------------------------------------

ml_data = pd.concat(
    [
        rfm[
            [
                "CustomerID",
                "Recency",
                "Frequency",
                "Monetary",
                "R_Score",
                "F_Score",
                "M_Score",
                "RFM_Score",
                "RFM_Total"
            ]
        ],
        X_scaled
    ],
    axis=1
)


# ---------------------------------------------------------
# 9. Display results
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("ML FEATURE PREPARATION COMPLETED")
print("=" * 60)

print(f"Customers prepared: {len(ml_data):,}")

print("\nML-ready feature sample:")

print(
    ml_data[
        [
            "CustomerID",
            "Recency_scaled",
            "Frequency_scaled",
            "Monetary_scaled"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 10. Check final missing values
# ---------------------------------------------------------

print("\nMissing values after preprocessing:")

print(
    ml_data[
        [
            "Recency_scaled",
            "Frequency_scaled",
            "Monetary_scaled"
        ]
    ].isnull().sum()
)


# ---------------------------------------------------------
# 11. Save ML-ready dataset
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

ml_data.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved ML-ready dataset to:")
print(OUTPUT_FILE)