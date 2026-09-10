import pandas as pd
from pathlib import Path


# =========================================================
# DATA PATHS
# =========================================================

DATA_DIR = Path("data/processed")

# Main active customer dataset
DATA_FILE = DATA_DIR / "customer_recommendations.csv"


# =========================================================
# LOAD CUSTOMER DATA
# =========================================================

def _load_customer_data():

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Customer data not found: {DATA_FILE}"
        )

    data = pd.read_csv(DATA_FILE)

    if data.empty:

        raise ValueError(
            "Customer dataset is empty."
        )

    return data


# =========================================================
# LOAD DATA WHEN APPLICATION STARTS
# =========================================================

customers_df = _load_customer_data()


# =========================================================
# RELOAD CUSTOMER DATA
# =========================================================

def reload_customer_data():
    """
    Reload the latest customer dataset from disk.

    This function is called after a new CSV dataset
    is uploaded and processed.
    """

    global customers_df

    customers_df = _load_customer_data()

    return customers_df


# =========================================================
# CONVERT DATAFRAME ROW → CUSTOMER DICTIONARY
# =========================================================

def customer_to_dict(row):

    return {

        "customer_id":
            int(row["CustomerID"]),

        "segment":
            str(row["Segment"]),

        "recency":
            int(row["Recency"]),

        "frequency":
            int(row["Frequency"]),

        "monetary":
            float(row["Monetary"]),

        "rfm_score":
            str(row["RFM_Score"]),

        "rfm_total":
            int(row["RFM_Total"]),

        "marketing_strategy":
            str(row.get("Marketing_Strategy", "")),

        "recommended_action":
            str(row.get("Recommended_Action", "")),

        "campaign":
            str(row.get("Campaign", "")),

        "priority":
            str(row.get("Priority", ""))
    }


# =========================================================
# GET CUSTOMER BY ID
# =========================================================

def get_customer(customer_id: int):

    customer = customers_df[
        customers_df["CustomerID"] == customer_id
    ]

    if not customer.empty:
        row = customer.iloc[0]
        return customer_to_dict(row)

    # Fallback to string comparison for CustomerID in dataframe
    try:
        match_str = customers_df[
            customers_df["CustomerID"].astype(str) == str(customer_id)
        ]
        if not match_str.empty:
            return customer_to_dict(match_str.iloc[0])
    except Exception:
        pass

    # Fallback to database lookup
    try:
        from app.database.connection import SessionLocal
        from app.database.models import Customer
        db = SessionLocal()
        try:
            db_cust = db.query(Customer).filter(
                Customer.customer_id == str(customer_id)
            ).first()
            if db_cust:
                return {
                    "customer_id": int(db_cust.customer_id) if str(db_cust.customer_id).isdigit() else db_cust.customer_id,
                    "segment": db_cust.segment or "Valued Customer",
                    "recency": int(db_cust.recency) if db_cust.recency is not None else 0,
                    "frequency": int(db_cust.frequency) if db_cust.frequency is not None else 0,
                    "monetary": float(db_cust.monetary) if db_cust.monetary is not None else 0.0,
                    "rfm_score": str(db_cust.rfm_score or ""),
                    "rfm_total": 0,
                    "marketing_strategy": getattr(db_cust, "campaign", "") or "Personalized engagement",
                    "recommended_action": getattr(db_cust, "action", "") or "Engage with personalized recommendations",
                    "campaign": getattr(db_cust, "campaign", "") or "Targeted Campaign",
                    "priority": getattr(db_cust, "priority", "") or "Medium",
                }
        finally:
            db.close()
    except Exception:
        pass

    return None


# =========================================================
# ALIAS
# =========================================================

def get_customer_by_id(customer_id: int):

    return get_customer(customer_id)


# =========================================================
# GET ALL CUSTOMERS
# =========================================================

def get_all_customers():

    customers = []

    for _, row in customers_df.iterrows():

        customers.append(
            customer_to_dict(row)
        )

    return customers


# =========================================================
# GET SEGMENT SUMMARY
# =========================================================

def get_segment_summary():

    required_columns = [
        "Segment",
        "CustomerID",
        "Recency",
        "Frequency",
        "Monetary"
    ]

    for column in required_columns:

        if column not in customers_df.columns:

            raise ValueError(
                f"Required column '{column}' is missing "
                f"from customer dataset."
            )

    summary = (

        customers_df

        .groupby("Segment")

        .agg(

            Customer_Count=(
                "CustomerID",
                "count"
            ),

            Avg_Recency=(
                "Recency",
                "mean"
            ),

            Avg_Frequency=(
                "Frequency",
                "mean"
            ),

            Avg_Monetary=(
                "Monetary",
                "mean"
            ),

            Total_Revenue=(
                "Monetary",
                "sum"
            )
        )

        .reset_index()
    )

    summaries = []

    for _, row in summary.iterrows():

        summaries.append({

            "segment":
                str(row["Segment"]),

            "customer_count":
                int(row["Customer_Count"]),

            "avg_recency":
                round(
                    float(row["Avg_Recency"]),
                    2
                ),

            "avg_frequency":
                round(
                    float(row["Avg_Frequency"]),
                    2
                ),

            "avg_monetary":
                round(
                    float(row["Avg_Monetary"]),
                    2
                ),

            "total_revenue":
                round(
                    float(row["Total_Revenue"]),
                    2
                )
        })

    return summaries


# =========================================================
# GET CUSTOMERS BY SEGMENT
# =========================================================

def get_customers_by_segment(segment: str):

    filtered = customers_df[
        customers_df["Segment"]
        .astype(str)
        .str.lower()
        .str.strip()
        ==
        segment.strip().lower()
    ]

    if filtered.empty:

        return []

    customers = []

    for _, row in filtered.iterrows():

        customers.append(
            customer_to_dict(row)
        )

    return customers


# =========================================================
# SEARCH CUSTOMERS
# =========================================================

def search_customers(query: str):

    query = query.strip()

    if not query:

        return []

    # -----------------------------------------------------
    # Numeric search → Customer ID
    # -----------------------------------------------------

    if query.isdigit():

        customer_id = int(query)

        filtered = customers_df[
            customers_df["CustomerID"] == customer_id
        ]

    # -----------------------------------------------------
    # Text search → Segment / Campaign
    # -----------------------------------------------------

    else:

        query_lower = query.lower()

        segment_match = (

            customers_df["Segment"]
            .astype(str)
            .str.lower()
            .str.contains(
                query_lower,
                na=False
            )
        )

        if "Campaign" in customers_df.columns:

            campaign_match = (

                customers_df["Campaign"]
                .astype(str)
                .str.lower()
                .str.contains(
                    query_lower,
                    na=False
                )
            )

        else:

            campaign_match = False

        filtered = customers_df[
            segment_match |
            campaign_match
        ]

    customers = []

    for _, row in filtered.iterrows():

        customers.append(
            customer_to_dict(row)
        )

    return customers


# =========================================================
# SORT CUSTOMERS
# =========================================================

def sort_customers(
    sort_by: str,
    order: str
):

    allowed_columns = {

        "monetary":
            "Monetary",

        "frequency":
            "Frequency",

        "recency":
            "Recency"
    }

    sort_by = sort_by.lower().strip()

    order = order.lower().strip()

    if sort_by not in allowed_columns:

        raise ValueError(
            "sort_by must be "
            "monetary, frequency, or recency"
        )

    if order not in [
        "asc",
        "desc"
    ]:

        raise ValueError(
            "order must be asc or desc"
        )

    column = allowed_columns[
        sort_by
    ]

    sorted_df = customers_df.sort_values(

        by=column,

        ascending=(
            order == "asc"
        )
    )

    customers = []

    for _, row in sorted_df.iterrows():

        customers.append(
            customer_to_dict(row)
        )

    return customers


# =========================================================
# GET CUSTOMERS BY PRIORITY
# =========================================================

def get_customers_by_priority(
    priority: str
):

    priority = (
        str(priority)
        .strip()
        .lower()
    )

    if "Priority" not in customers_df.columns:

        return []

    priority_series = (

        customers_df["Priority"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    filtered = customers_df[
        priority_series == priority
    ]

    if filtered.empty:

        return []

    customers = []

    for _, row in filtered.iterrows():

        customers.append(
            customer_to_dict(row)
        )

    return customers


# =========================================================
# GET CAMPAIGN SUMMARY
# =========================================================

def get_campaign_summary():

    if "Campaign" not in customers_df.columns:

        return []

    campaign_summary = (

        customers_df

        .groupby("Campaign")

        .agg(

            Customer_Count=(
                "CustomerID",
                "count"
            ),

            Total_Revenue=(
                "Monetary",
                "sum"
            )
        )

        .reset_index()
    )

    campaigns = []

    for _, row in campaign_summary.iterrows():

        campaigns.append({

            "campaign":
                str(row["Campaign"]),

            "customer_count":
                int(row["Customer_Count"]),

            "total_revenue":
                float(row["Total_Revenue"])
        })

    return campaigns


# =========================================================
# GET PRIORITY SUMMARY
# =========================================================

def get_priority_summary():

    if "Priority" not in customers_df.columns:

        return []

    priority_summary = (

        customers_df

        .groupby("Priority")

        .agg(

            Customer_Count=(
                "CustomerID",
                "count"
            ),

            Total_Revenue=(
                "Monetary",
                "sum"
            )
        )

        .reset_index()
    )

    priorities = []

    for _, row in priority_summary.iterrows():

        priorities.append({

            "priority":
                str(row["Priority"]),

            "customer_count":
                int(row["Customer_Count"]),

            "total_revenue":
                float(row["Total_Revenue"])
        })

    return priorities


# =========================================================
# GET CUSTOMER STATISTICS
# =========================================================

def get_customer_statistics():

    total_customers = int(
        len(customers_df)
    )

    total_revenue = float(
        customers_df["Monetary"].sum()
    )

    average_monetary = float(
        customers_df["Monetary"].mean()
    )

    total_segments = int(
        customers_df["Segment"].nunique()
    )

    return {

        "total_customers":
            total_customers,

        "total_revenue":
            total_revenue,

        "average_monetary":
            average_monetary,

        "total_segments":
            total_segments
    }


# =========================================================
# GET DASHBOARD OVERVIEW
# =========================================================

def get_dashboard_overview():

    # -----------------------------------------------------
    # BASIC KPI VALUES
    # -----------------------------------------------------

    total_customers = int(
        len(customers_df)
    )

    total_revenue = float(
        customers_df["Monetary"].sum()
    )

    average_customer_value = float(
        customers_df["Monetary"].mean()
    )

    total_segments = int(
        customers_df["Segment"].nunique()
    )

    # -----------------------------------------------------
    # CAMPAIGNS
    # -----------------------------------------------------

    if "Campaign" in customers_df.columns:

        total_campaigns = int(
            customers_df["Campaign"]
            .dropna()
            .nunique()
        )

    else:

        total_campaigns = 0

    # -----------------------------------------------------
    # HIGH PRIORITY CUSTOMERS
    # -----------------------------------------------------

    if "Priority" in customers_df.columns:

        priority_values = (

            customers_df["Priority"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        high_priority_customers = int(

            (
                priority_values == "high"
            ).sum()
        )

    else:

        high_priority_customers = 0

    # -----------------------------------------------------
    # SEGMENT ANALYTICS
    # -----------------------------------------------------

    segments = get_segment_summary()

    # -----------------------------------------------------
    # RETURN COMPLETE DASHBOARD RESPONSE
    # -----------------------------------------------------

    return {

        "total_customers":
            total_customers,

        "total_revenue":
            total_revenue,

        "average_customer_value":
            average_customer_value,

        "total_segments":
            total_segments,

        "total_campaigns":
            total_campaigns,

        "high_priority_customers":
            high_priority_customers,

        "segments":
            segments,

        "segment_data":
            segments
    }