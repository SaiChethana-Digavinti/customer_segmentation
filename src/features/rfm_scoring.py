import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/rfm_customer_data.csv"
)

OUTPUT_FILE = Path(
    "data/processed/rfm_scored_customers.csv"
)


# ---------------------------------------------------------
# 2. Load RFM data
# ---------------------------------------------------------

print("Loading RFM data...")

rfm = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(rfm):,}")


# ---------------------------------------------------------
# 3. Create RFM scores
# ---------------------------------------------------------

# Recency:
# Lower value = better customer
rfm["R_Score"] = pd.qcut(
    rfm["Recency"],
    q=5,
    labels=[5, 4, 3, 2, 1],
    duplicates="drop"
).astype(int)


# Frequency:
# Higher value = better customer
rfm["F_Score"] = pd.qcut(
    rfm["Frequency"].rank(method="first"),
    q=5,
    labels=[1, 2, 3, 4, 5]
).astype(int)


# Monetary:
# Higher value = better customer
rfm["M_Score"] = pd.qcut(
    rfm["Monetary"].rank(method="first"),
    q=5,
    labels=[1, 2, 3, 4, 5]
).astype(int)


# ---------------------------------------------------------
# 4. Create combined RFM score
# ---------------------------------------------------------

rfm["RFM_Score"] = (
    rfm["R_Score"].astype(str)
    + rfm["F_Score"].astype(str)
    + rfm["M_Score"].astype(str)
)


# Numerical overall score
rfm["RFM_Total"] = (
    rfm["R_Score"]
    + rfm["F_Score"]
    + rfm["M_Score"]
)


# ---------------------------------------------------------
# 5. Display results
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("RFM SCORING COMPLETED")
print("=" * 60)

print(f"Customers scored: {len(rfm):,}")

print("\nSample scored customers:")

print(
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
    ]
    .head(10)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 6. Score distribution
# ---------------------------------------------------------

print("\nRFM Total Score Distribution:")

print(
    rfm["RFM_Total"]
    .value_counts()
    .sort_index()
)


# ---------------------------------------------------------
# 7. Save scored dataset
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

rfm.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved scored RFM dataset to:")
print(OUTPUT_FILE)