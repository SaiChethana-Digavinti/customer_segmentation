import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/cleaned_transactions.csv"
)

OUTPUT_FILE = Path(
    "data/processed/rfm_customer_data.csv"
)


# ---------------------------------------------------------
# 2. Load cleaned transaction data
# ---------------------------------------------------------

print("Loading cleaned transaction data...")

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["InvoiceDate"]
)

print(f"Transactions loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Define analysis/reference date
# ---------------------------------------------------------

reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

print(f"Reference date: {reference_date}")


# ---------------------------------------------------------
# 4. Calculate RFM metrics
# ---------------------------------------------------------

rfm = df.groupby("CustomerID").agg(
    Recency=(
        "InvoiceDate",
        lambda x: (reference_date - x.max()).days
    ),
    Frequency=(
        "InvoiceNo",
        "nunique"
    ),
    Monetary=(
        "TotalAmount",
        "sum"
    )
).reset_index()


# ---------------------------------------------------------
# 5. Round monetary values
# ---------------------------------------------------------

rfm["Monetary"] = rfm["Monetary"].round(2)


# ---------------------------------------------------------
# 6. Display RFM summary
# ---------------------------------------------------------

print("\n" + "=" * 50)
print("RFM ANALYSIS COMPLETED")
print("=" * 50)

print(f"Customers analyzed: {len(rfm):,}")

print("\nRFM data:")
print(rfm.head(10).to_string(index=False))


# ---------------------------------------------------------
# 7. Display descriptive statistics
# ---------------------------------------------------------

print("\nRFM statistics:")
print(rfm[["Recency", "Frequency", "Monetary"]].describe())


# ---------------------------------------------------------
# 8. Check for missing values
# ---------------------------------------------------------

print("\nMissing values:")
print(rfm.isnull().sum())


# ---------------------------------------------------------
# 9. Save RFM dataset
# ---------------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

rfm.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nRFM dataset saved to:")
print(OUTPUT_FILE)