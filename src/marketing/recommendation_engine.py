import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/final_customer_segments.csv"
)

OUTPUT_FILE = Path(
    "data/processed/customer_recommendations.csv"
)


# ---------------------------------------------------------
# 2. Load customer segmentation data
# ---------------------------------------------------------

print("Loading customer segmentation data...")

df = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Recommendation rules
# ---------------------------------------------------------

recommendations = {

    "Champions": {
        "Strategy": "Loyalty and premium engagement",
        "Action": "Offer exclusive products, VIP rewards, early access, and premium services.",
        "Campaign": "VIP Loyalty Campaign",
        "Priority": "High"
    },

    "Loyal Customers": {
        "Strategy": "Cross-selling and upselling",
        "Action": "Recommend complementary products and provide exclusive member offers.",
        "Campaign": "Loyal Customer Campaign",
        "Priority": "Medium"
    },

    "New Customers": {
        "Strategy": "Customer onboarding and retention",
        "Action": "Provide welcome offers and incentives for the second purchase.",
        "Campaign": "New Customer Welcome Campaign",
        "Priority": "High"
    },

    "At Risk": {
        "Strategy": "Customer win-back",
        "Action": "Send personalized discounts, product reminders, and re-engagement offers.",
        "Campaign": "Win-Back Campaign",
        "Priority": "Very High"
    }
}


# ---------------------------------------------------------
# 4. Create recommendation columns
# ---------------------------------------------------------

df["Marketing_Strategy"] = df["Segment"].map(
    lambda segment: recommendations[segment]["Strategy"]
)

df["Recommended_Action"] = df["Segment"].map(
    lambda segment: recommendations[segment]["Action"]
)

df["Campaign"] = df["Segment"].map(
    lambda segment: recommendations[segment]["Campaign"]
)

df["Priority"] = df["Segment"].map(
    lambda segment: recommendations[segment]["Priority"]
)


# ---------------------------------------------------------
# 5. Validate recommendations
# ---------------------------------------------------------

missing_recommendations = (
    df["Marketing_Strategy"].isna().sum()
)

print(
    f"\nCustomers without recommendations: "
    f"{missing_recommendations}"
)


# ---------------------------------------------------------
# 6. Display sample recommendations
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("SAMPLE CUSTOMER RECOMMENDATIONS")
print("=" * 70)

print(
    df[
        [
            "CustomerID",
            "Segment",
            "Marketing_Strategy",
            "Recommended_Action",
            "Campaign",
            "Priority"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 7. Segment-level recommendation summary
# ---------------------------------------------------------

summary = (
    df.groupby(
        [
            "Segment",
            "Marketing_Strategy",
            "Campaign",
            "Priority"
        ]
    )
    .agg(
        Customer_Count=("CustomerID", "count"),
        Total_Revenue=("Monetary", "sum")
    )
    .round(2)
    .reset_index()
)


print("\n" + "=" * 70)
print("MARKETING RECOMMENDATION SUMMARY")
print("=" * 70)

print(
    summary.to_string(index=False)
)


# ---------------------------------------------------------
# 8. Save customer recommendations
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
# 9. Save recommendation summary
# ---------------------------------------------------------

SUMMARY_FILE = Path(
    "data/processed/recommendation_summary.csv"
)

summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ---------------------------------------------------------
# 10. Final output
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("RECOMMENDATION ENGINE COMPLETED")
print("=" * 70)

print(
    f"Customers processed: {len(df):,}"
)

print("\nCustomer recommendations saved to:")
print(OUTPUT_FILE)

print("\nRecommendation summary saved to:")
print(SUMMARY_FILE)