import pandas as pd


# ============================================================
# CUSTOMER SEGMENTATION SERVICE
# ============================================================
#
# Responsibility:
# Convert RFM + clustering information into
# business-friendly customer segments.
#
# Clustering is NOT performed here.
#
# Clustering is handled by:
# app.services.clustering_service
#
# This separation makes the project cleaner and
# more suitable for an industry-style architecture.
# ============================================================


def segment_customers(
    rfm: pd.DataFrame
) -> pd.DataFrame:

    # ========================================================
    # 1. COPY INPUT DATA
    # ========================================================

    data = rfm.copy()

    # ========================================================
    # 2. VALIDATE REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "CustomerID",
        "Recency",
        "Frequency",
        "Monetary"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    if len(data) < 2:

        raise ValueError(
            "At least 2 customers are required "
            "for segmentation."
        )

    # ========================================================
    # 3. CLEAN RFM VALUES
    # ========================================================

    for column in [
        "Recency",
        "Frequency",
        "Monetary"
    ]:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    data[
        [
            "Recency",
            "Frequency",
            "Monetary"
        ]
    ] = data[
        [
            "Recency",
            "Frequency",
            "Monetary"
        ]
    ].fillna(0)

    # ========================================================
    # 4. INITIAL SEGMENT
    # ========================================================
    #
    # Customers that do not match a stronger rule
    # will remain Potential Loyalists.
    # ========================================================

    data["Segment"] = "Potential Loyalists"

    # ========================================================
    # 5. MONETARY THRESHOLD
    # ========================================================
    #
    # Median monetary value is used as a business
    # threshold for identifying higher-value customers.
    # ========================================================

    monetary_50 = data[
        "Monetary"
    ].quantile(0.50)

    # ========================================================
    # 6. NEW CUSTOMERS
    # ========================================================
    #
    # Recently purchased
    # Low purchase frequency
    # ========================================================

    new_customer_condition = (
        (data["Recency"] <= 30)
        &
        (data["Frequency"] <= 2)
    )

    data.loc[
        new_customer_condition,
        "Segment"
    ] = "New Customers"

    # ========================================================
    # 7. LOST CUSTOMERS
    # ========================================================
    #
    # Long time since purchase
    # Low purchase frequency
    # ========================================================

    lost_customer_condition = (
        (data["Recency"] > 90)
        &
        (data["Frequency"] <= 2)
    )

    data.loc[
        lost_customer_condition,
        "Segment"
    ] = "Lost Customers"

    # ========================================================
    # 8. AT RISK CUSTOMERS
    # ========================================================
    #
    # Customer purchased previously but has not
    # purchased recently.
    # ========================================================

    at_risk_condition = (
        (data["Recency"] > 60)
        &
        (data["Recency"] <= 90)
        &
        (data["Frequency"] >= 2)
    )

    data.loc[
        at_risk_condition,
        "Segment"
    ] = "At Risk"

    # ========================================================
    # 9. CHAMPIONS
    # ========================================================
    #
    # Recent
    # Frequent
    # Higher monetary value
    #
    # Champions are intentionally assigned after
    # New Customers and At Risk rules so that
    # high-value customers receive the stronger segment.
    # ========================================================

    champion_condition = (
        (data["Recency"] <= 60)
        &
        (data["Frequency"] >= 2)
        &
        (data["Monetary"] >= monetary_50)
    )

    data.loc[
        champion_condition,
        "Segment"
    ] = "Champions"

    # ========================================================
    # 10. LOYAL CUSTOMERS
    # ========================================================
    #
    # Recent
    # Reasonably frequent
    # Not already Champions
    # ========================================================

    loyal_condition = (
        (data["Recency"] <= 60)
        &
        (data["Frequency"] >= 2)
        &
        (data["Segment"] != "Champions")
    )

    data.loc[
        loyal_condition,
        "Segment"
    ] = "Loyal Customers"

    # ========================================================
    # 11. CLUSTER INFORMATION
    # ========================================================
    #
    # If clustering_service.py has already run,
    # preserve its information.
    #
    # We DO NOT calculate clusters here.
    # ========================================================

    clustering_columns = [
        "Cluster",
        "Clustering_Method",
        "Silhouette_Score",
        "PCA1",
        "PCA2"
    ]

    for column in clustering_columns:

        if column not in data.columns:

            if column == "Cluster":

                data[column] = None

            elif column == "Clustering_Method":

                data[column] = None

            elif column == "Silhouette_Score":

                data[column] = None

            else:

                data[column] = None

    # ========================================================
    # 12. SEGMENT PRIORITY
    # ========================================================
    #
    # Business priority helps marketing teams decide
    # which customers should receive attention first.
    # ========================================================

    priority_mapping = {

        "Champions":
            "Very High",

        "Loyal Customers":
            "High",

        "Potential Loyalists":
            "Medium",

        "New Customers":
            "Medium",

        "At Risk":
            "High",

        "Lost Customers":
            "Low"
    }

    data["Priority"] = (
        data["Segment"]
        .map(priority_mapping)
        .fillna("Medium")
    )

    # ========================================================
    # 13. CAMPAIGN RECOMMENDATION
    # ========================================================

    campaign_mapping = {

        "Champions":
            "VIP Loyalty Campaign",

        "Loyal Customers":
            "Loyalty Rewards Campaign",

        "Potential Loyalists":
            "Engagement Campaign",

        "New Customers":
            "Welcome Campaign",

        "At Risk":
            "Win Back Campaign",

        "Lost Customers":
            "Reactivation Campaign"
    }

    data["Campaign"] = (
        data["Segment"]
        .map(campaign_mapping)
        .fillna("General Marketing Campaign")
    )

    # ========================================================
    # 14. MARKETING STRATEGY
    # ========================================================

    strategy_mapping = {

        "Champions":
            (
                "Provide VIP benefits, early access, "
                "exclusive products and premium rewards."
            ),

        "Loyal Customers":
            (
                "Strengthen loyalty using rewards, "
                "personalized offers and repeat-purchase incentives."
            ),

        "Potential Loyalists":
            (
                "Increase engagement with personalized "
                "recommendations and targeted promotions."
            ),

        "New Customers":
            (
                "Build the relationship through onboarding, "
                "welcome offers and product recommendations."
            ),

        "At Risk":
            (
                "Use personalized discounts and reminders "
                "to encourage another purchase."
            ),

        "Lost Customers":
            (
                "Launch reactivation campaigns with "
                "strong incentives and personalized offers."
            )
    }

    data["Marketing_Strategy"] = (
        data["Segment"]
        .map(strategy_mapping)
        .fillna(
            "Use personalized marketing based on customer behavior."
        )
    )

    # ========================================================
    # 15. RECOMMENDED ACTION
    # ========================================================

    action_mapping = {

        "Champions":
            "Reward and retain high-value customers.",

        "Loyal Customers":
            "Increase retention and encourage repeat purchases.",

        "Potential Loyalists":
            "Convert customers into loyal repeat buyers.",

        "New Customers":
            "Encourage the second purchase.",

        "At Risk":
            "Prevent customer churn with a targeted win-back offer.",

        "Lost Customers":
            "Attempt customer reactivation with a personalized offer."
    }

    data["Recommended_Action"] = (
        data["Segment"]
        .map(action_mapping)
        .fillna(
            "Create a personalized customer engagement strategy."
        )
    )

    # ========================================================
    # 16. RFM SCORE
    # ========================================================
    #
    # Generate a simple 1-5 RFM score for each customer.
    #
    # Recency:
    # Lower is better.
    #
    # Frequency:
    # Higher is better.
    #
    # Monetary:
    # Higher is better.
    # ========================================================

    try:

        data["R_Score"] = pd.qcut(
            data["Recency"].rank(
                method="first"
            ),
            5,
            labels=False
        ) + 1

        # Reverse Recency score
        data["R_Score"] = (
            6 - data["R_Score"]
        )

        data["F_Score"] = pd.qcut(
            data["Frequency"].rank(
                method="first"
            ),
            5,
            labels=False
        ) + 1

        data["M_Score"] = pd.qcut(
            data["Monetary"].rank(
                method="first"
            ),
            5,
            labels=False
        ) + 1

        data["RFM_Score"] = (
            data["R_Score"].astype(str)
            +
            data["F_Score"].astype(str)
            +
            data["M_Score"].astype(str)
        )

        data["RFM_Total"] = (
            data["R_Score"]
            +
            data["F_Score"]
            +
            data["M_Score"]
        )

        data = data.drop(
            columns=[
                "R_Score",
                "F_Score",
                "M_Score"
            ]
        )

    except Exception:

        data["RFM_Score"] = None
        data["RFM_Total"] = None

    # ========================================================
    # 17. SEGMENT SORTING
    # ========================================================

    segment_order = {

        "Champions": 1,

        "Loyal Customers": 2,

        "Potential Loyalists": 3,

        "New Customers": 4,

        "At Risk": 5,

        "Lost Customers": 6,

        "Other Customers": 7
    }

    data["_segment_order"] = (
        data["Segment"]
        .map(segment_order)
        .fillna(99)
    )

    data = data.sort_values(
        by=[
            "_segment_order",
            "Monetary"
        ],
        ascending=[
            True,
            False
        ]
    )

    # ========================================================
    # 18. REMOVE TEMPORARY COLUMN
    # ========================================================

    data = data.drop(
        columns=[
            "_segment_order"
        ]
    )

    # ========================================================
    # 19. RESET INDEX
    # ========================================================

    data = data.reset_index(
        drop=True
    )

    # ========================================================
    # 20. RETURN
    # ========================================================

    return data