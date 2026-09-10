import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/ml_ready_features.csv"
)

OUTPUT_FILE = Path(
    "data/processed/customer_segments.csv"
)


# ---------------------------------------------------------
# 2. Load ML-ready data
# ---------------------------------------------------------

print("Loading ML-ready customer data...")

df = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Select features for K-Means
# ---------------------------------------------------------

features = [
    "Recency_scaled",
    "Frequency_scaled",
    "Monetary_scaled"
]

X = df[features]


# ---------------------------------------------------------
# 4. Create K-Means model
# ---------------------------------------------------------

K = 4

print(f"\nTraining K-Means with K = {K}...")


kmeans = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=10
)


# ---------------------------------------------------------
# 5. Train model and predict clusters
# ---------------------------------------------------------

df["Cluster"] = kmeans.fit_predict(X)


# ---------------------------------------------------------
# 6. Display cluster counts
# ---------------------------------------------------------

print("\nCluster distribution:")

print(
    df["Cluster"]
    .value_counts()
    .sort_index()
)


# ---------------------------------------------------------
# 7. Calculate cluster profiles
# ---------------------------------------------------------

cluster_profile = (
    df.groupby("Cluster")
    .agg(
        Customer_Count=("CustomerID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean")
    )
    .round(2)
    .reset_index()
)


# ---------------------------------------------------------
# 8. Display cluster profiles
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("CUSTOMER CLUSTER PROFILES")
print("=" * 65)

print(
    cluster_profile.to_string(
        index=False
    )
)


# ---------------------------------------------------------
# 9. Save customer segments
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 10. Save cluster profile
# ---------------------------------------------------------

PROFILE_FILE = Path(
    "data/processed/cluster_profiles.csv"
)

cluster_profile.to_csv(
    PROFILE_FILE,
    index=False
)


# ---------------------------------------------------------
# 11. Display model information
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("K-MEANS CLUSTERING COMPLETED")
print("=" * 65)

print(f"Number of clusters: {K}")
print(f"Customers segmented: {len(df):,}")

print("\nCustomer segments saved to:")
print(OUTPUT_FILE)

print("\nCluster profiles saved to:")
print(PROFILE_FILE)