import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/customer_segments.csv"
)

OUTPUT_FILE = Path(
    "data/processed/final_customer_segments.csv"
)


# ---------------------------------------------------------
# 2. Load clustered customer data
# ---------------------------------------------------------

print("Loading customer cluster data...")

df = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Define business segment names
# ---------------------------------------------------------

segment_names = {
    0: "Champions",
    1: "At Risk",
    2: "New Customers",
    3: "Loyal Customers"
}


# ---------------------------------------------------------
# 4. Define marketing strategies
# ---------------------------------------------------------

marketing_strategies = {
    "Champions":
        "Target with premium products, exclusive offers, and loyalty rewards.",

    "At Risk":
        "Launch win-back campaigns with personalized offers and re-engagement discounts.",

    "New Customers":
        "Use welcome offers and second-purchase incentives to build loyalty.",

    "Loyal Customers":
        "Use cross-selling, upselling, and exclusive member offers."
}


# ---------------------------------------------------------
# 5. Add segment names
# ---------------------------------------------------------

df["Segment"] = df["Cluster"].map(
    segment_names
)


# ---------------------------------------------------------
# 6. Add marketing recommendations
# ---------------------------------------------------------

df["Marketing_Recommendation"] = (
    df["Segment"].map(marketing_strategies)
)


# ---------------------------------------------------------
# 7. Validate segment assignment
# ---------------------------------------------------------

missing_segments = df["Segment"].isna().sum()

print(
    f"\nCustomers without a segment: "
    f"{missing_segments}"
)


# ---------------------------------------------------------
# 8. Display segment distribution
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("CUSTOMER SEGMENT DISTRIBUTION")
print("=" * 65)

print(
    df["Segment"]
    .value_counts()
)


# ---------------------------------------------------------
# 9. Display segment summary
# ---------------------------------------------------------

segment_summary = (
    df.groupby("Segment")
    .agg(
        Customer_Count=("CustomerID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean")
    )
    .round(2)
    .reset_index()
)


print("\nSegment summary:")

print(
    segment_summary.to_string(
        index=False
    )
)


# ---------------------------------------------------------
# 10. Save final segmentation dataset
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
# 11. Save segment summary
# ---------------------------------------------------------

SUMMARY_FILE = Path(
    "data/processed/segment_summary.csv"
)

segment_summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ---------------------------------------------------------
# 12. Final output
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("BUSINESS SEGMENTATION COMPLETED")
print("=" * 65)

print(
    f"Total customers segmented: "
    f"{len(df):,}"
)

print("\nFinal dataset:")
print(OUTPUT_FILE)

print("\nSegment summary:")
print(SUMMARY_FILE)