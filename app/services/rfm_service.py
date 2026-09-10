import pandas as pd


def calculate_rfm(
    df: pd.DataFrame,
    customer_id_column: str,
    date_column: str,
    amount_column: str
):

    # ---------------------------------------------------------
    # Create a working copy
    # ---------------------------------------------------------

    data = df.copy()

    # ---------------------------------------------------------
    # Keep only required columns
    # ---------------------------------------------------------

    data = data[
        [
            customer_id_column,
            date_column,
            amount_column
        ]
    ].copy()

    # ---------------------------------------------------------
    # Convert date column
    # ---------------------------------------------------------

    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce"
    )

    # ---------------------------------------------------------
    # Convert amount column to numeric
    # ---------------------------------------------------------

    data[amount_column] = pd.to_numeric(
        data[amount_column],
        errors="coerce"
    )

    # ---------------------------------------------------------
    # Remove invalid rows
    # ---------------------------------------------------------

    data = data.dropna(
        subset=[
            customer_id_column,
            date_column,
            amount_column
        ]
    )

    if data.empty:
        raise ValueError(
            "No valid customer transaction data found."
        )

    # ---------------------------------------------------------
    # Reference date
    # Latest transaction date + 1 day
    # ---------------------------------------------------------

    reference_date = (
        data[date_column].max()
        + pd.Timedelta(days=1)
    )

    # ---------------------------------------------------------
    # Calculate RFM
    # ---------------------------------------------------------

    rfm = (
        data
        .groupby(customer_id_column)
        .agg(

            Recency=(
                date_column,
                lambda x:
                    (reference_date - x.max()).days
            ),

            Frequency=(
                date_column,
                "count"
            ),

            Monetary=(
                amount_column,
                "sum"
            )

        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Rename customer ID
    # ---------------------------------------------------------

    rfm = rfm.rename(
        columns={
            customer_id_column: "CustomerID"
        }
    )

    # ---------------------------------------------------------
    # Round monetary value
    # ---------------------------------------------------------

    rfm["Monetary"] = rfm[
        "Monetary"
    ].round(2)

    # ---------------------------------------------------------
    # RFM Scores
    # ---------------------------------------------------------

    # Recency:
    # Lower recency = better customer

    try:

        rfm["R_Score"] = pd.qcut(
            rfm["Recency"],
            q=5,
            labels=[5, 4, 3, 2, 1],
            duplicates="drop"
        )

    except ValueError:

        rfm["R_Score"] = 3

    # Frequency:
    # Higher frequency = better customer

    try:

        rfm["F_Score"] = pd.qcut(
            rfm["Frequency"].rank(
                method="first"
            ),
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates="drop"
        )

    except ValueError:

        rfm["F_Score"] = 3

    # Monetary:
    # Higher monetary value = better customer

    try:

        rfm["M_Score"] = pd.qcut(
            rfm["Monetary"].rank(
                method="first"
            ),
            q=5,
            labels=[1, 2, 3, 4, 5],
            duplicates="drop"
        )

    except ValueError:

        rfm["M_Score"] = 3

    # ---------------------------------------------------------
    # Convert scores to integers
    # ---------------------------------------------------------

    rfm["R_Score"] = rfm[
        "R_Score"
    ].astype(int)

    rfm["F_Score"] = rfm[
        "F_Score"
    ].astype(int)

    rfm["M_Score"] = rfm[
        "M_Score"
    ].astype(int)

    # ---------------------------------------------------------
    # Combined RFM Score
    # ---------------------------------------------------------

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )

    # ---------------------------------------------------------
    # Numeric overall score
    # ---------------------------------------------------------

    rfm["RFM_Total"] = (
        rfm["R_Score"]
        + rfm["F_Score"]
        + rfm["M_Score"]
    )

    # ---------------------------------------------------------
    # Customer segment
    # ---------------------------------------------------------

    def assign_segment(row):

        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        # Best customers
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"

        # Loyal customers
        elif f >= 4 and r >= 3:
            return "Loyal Customers"

        # High spending but not frequent
        elif m >= 4 and f <= 3:
            return "Big Spenders"

        # Recent customers
        elif r >= 4 and f <= 2:
            return "New Customers"

        # Customers becoming inactive
        elif r <= 2 and f >= 3:
            return "At Risk"

        # Low engagement
        elif r <= 2 and f <= 2 and m <= 2:
            return "Lost Customers"

        # Everyone else
        else:
            return "Potential Loyalists"

    rfm["Segment"] = rfm.apply(
        assign_segment,
        axis=1
    )

    # ---------------------------------------------------------
    # Sort by RFM total
    # ---------------------------------------------------------

    rfm = rfm.sort_values(
        by="RFM_Total",
        ascending=False
    )

    # ---------------------------------------------------------
    # Reset index
    # ---------------------------------------------------------

    rfm = rfm.reset_index(
        drop=True
    )

    return rfm