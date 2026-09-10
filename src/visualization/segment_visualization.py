import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/final_customer_segments.csv"
)

OUTPUT_DIR = Path(
    "data/processed/visualizations"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# 2. Load final customer segmentation data
# ---------------------------------------------------------

print("Loading final customer segmentation data...")

df = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Customer count by segment
# ---------------------------------------------------------

segment_counts = (
    df["Segment"]
    .value_counts()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 6))

segment_counts.plot(
    kind="bar"
)

plt.title(
    "Customer Distribution by Segment"
)

plt.xlabel("Customer Segment")
plt.ylabel("Number of Customers")

plt.xticks(
    rotation=20,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "customer_distribution.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 4. Revenue by segment
# ---------------------------------------------------------

revenue_by_segment = (
    df.groupby("Segment")["Monetary"]
    .sum()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 6))

revenue_by_segment.plot(
    kind="bar"
)

plt.title(
    "Revenue Contribution by Customer Segment"
)

plt.xlabel("Customer Segment")
plt.ylabel("Total Revenue")

plt.xticks(
    rotation=20,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "revenue_by_segment.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 5. Recency vs Monetary
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

for segment in df["Segment"].unique():

    segment_data = df[
        df["Segment"] == segment
    ]

    plt.scatter(
        segment_data["Recency"],
        segment_data["Monetary"],
        label=segment,
        alpha=0.6
    )

plt.title(
    "Recency vs Monetary Value"
)

plt.xlabel("Recency (Days)")
plt.ylabel("Monetary Value")

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "recency_vs_monetary.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 6. Frequency vs Monetary
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

for segment in df["Segment"].unique():

    segment_data = df[
        df["Segment"] == segment
    ]

    plt.scatter(
        segment_data["Frequency"],
        segment_data["Monetary"],
        label=segment,
        alpha=0.6
    )

plt.title(
    "Frequency vs Monetary Value"
)

plt.xlabel("Purchase Frequency")
plt.ylabel("Monetary Value")

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "frequency_vs_monetary.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 7. Segment summary
# ---------------------------------------------------------

summary = (
    df.groupby("Segment")
    .agg(
        Customer_Count=("CustomerID", "count"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Avg_Monetary=("Monetary", "mean"),
        Total_Revenue=("Monetary", "sum")
    )
    .round(2)
    .reset_index()
)

summary.to_csv(
    OUTPUT_DIR / "visualization_summary.csv",
    index=False
)


# ---------------------------------------------------------
# 8. Final output
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("VISUALIZATION GENERATION COMPLETED")
print("=" * 60)

print("\nGenerated files:")

print(
    OUTPUT_DIR / "customer_distribution.png"
)

print(
    OUTPUT_DIR / "revenue_by_segment.png"
)

print(
    OUTPUT_DIR / "recency_vs_monetary.png"
)

print(
    OUTPUT_DIR / "frequency_vs_monetary.png"
)

print(
    OUTPUT_DIR / "visualization_summary.csv"
)