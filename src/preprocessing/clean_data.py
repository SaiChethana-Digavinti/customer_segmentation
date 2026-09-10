import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/raw/UCI online retail dataset/Online Retail.xlsx"
)

OUTPUT_FILE = Path(
    "data/processed/cleaned_transactions.csv"
)


# ---------------------------------------------------------
# 2. Load dataset
# ---------------------------------------------------------

print("Loading dataset...")

df = pd.read_excel(INPUT_FILE)

print(f"Original rows: {len(df):,}")


# ---------------------------------------------------------
# 3. Remove duplicate transactions
# ---------------------------------------------------------

duplicate_count = df.duplicated().sum()

print(f"Duplicate rows found: {duplicate_count:,}")

df = df.drop_duplicates()


# ---------------------------------------------------------
# 4. Remove transactions without CustomerID
# ---------------------------------------------------------

missing_customer_count = df["CustomerID"].isna().sum()

print(
    f"Rows with missing CustomerID: "
    f"{missing_customer_count:,}"
)

df = df.dropna(subset=["CustomerID"])


# ---------------------------------------------------------
# 5. Remove cancelled invoices
# ---------------------------------------------------------

cancelled_count = df["InvoiceNo"].astype(str).str.startswith("C").sum()

print(f"Cancelled transactions found: {cancelled_count:,}")

df = df[
    ~df["InvoiceNo"].astype(str).str.startswith("C")
]


# ---------------------------------------------------------
# 6. Remove invalid quantities
# ---------------------------------------------------------

invalid_quantity_count = (df["Quantity"] <= 0).sum()

print(
    f"Rows with invalid Quantity: "
    f"{invalid_quantity_count:,}"
)

df = df[df["Quantity"] > 0]


# ---------------------------------------------------------
# 7. Remove invalid prices
# ---------------------------------------------------------

invalid_price_count = (df["UnitPrice"] <= 0).sum()

print(
    f"Rows with invalid UnitPrice: "
    f"{invalid_price_count:,}"
)

df = df[df["UnitPrice"] > 0]


# ---------------------------------------------------------
# 8. Handle missing descriptions
# ---------------------------------------------------------

df["Description"] = df["Description"].fillna("Unknown")


# ---------------------------------------------------------
# 9. Make CustomerID an integer
# ---------------------------------------------------------

df["CustomerID"] = df["CustomerID"].astype(int)


# ---------------------------------------------------------
# 10. Create TotalAmount
# ---------------------------------------------------------

df["TotalAmount"] = (
    df["Quantity"] * df["UnitPrice"]
)


# ---------------------------------------------------------
# 11. Sort transactions
# ---------------------------------------------------------

df = df.sort_values(
    by=["CustomerID", "InvoiceDate"]
).reset_index(drop=True)


# ---------------------------------------------------------
# 12. Save cleaned dataset
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
# 13. Final summary
# ---------------------------------------------------------

print("\n" + "=" * 50)
print("DATA CLEANING COMPLETED")
print("=" * 50)

print(f"Final rows: {len(df):,}")
print(f"Final columns: {len(df.columns)}")
print(f"Unique customers: {df['CustomerID'].nunique():,}")

print(
    f"Date range: "
    f"{df['InvoiceDate'].min()} "
    f"to "
    f"{df['InvoiceDate'].max()}"
)

print(
    f"Total revenue: "
    f"{df['TotalAmount'].sum():,.2f}"
)

print("\nSaved cleaned dataset to:")
print(OUTPUT_FILE)